"""Read-only adapters for explicitly configured public commerce evidence feeds.

No sources are enabled by default. URLs are restricted to configured HTTPS hosts;
requests are GET-only and response sizes are bounded. Feed records are leads/evidence,
not proof of stock, demand, product authenticity or commercial availability.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
import re
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


USER_AGENT = "ULTRON-ReadOnly-Commerce-Research/1.0"
MAX_RESPONSE_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 12.0


@dataclass(frozen=True)
class SourceDefinition:
    name: str
    kind: str
    url: str
    allowed_hosts: tuple[str, ...]
    enabled: bool = True
    max_records: int = 25

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("source name must not be empty")
        if self.kind not in {"product_rss", "demand_rss", "supplier_json"}:
            raise ValueError("unsupported source kind")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("source URL must use HTTPS")
        hosts = tuple(host.lower().rstrip(".") for host in self.allowed_hosts)
        if not hosts or parsed.hostname.lower().rstrip(".") not in hosts:
            raise ValueError("source host must be explicitly allowlisted")
        if any(not host or "/" in host or ":" in host for host in hosts):
            raise ValueError("allowed_hosts must contain hostnames only")
        if type(self.max_records) is not int or not 1 <= self.max_records <= 100:
            raise ValueError("max_records must be between 1 and 100")


@dataclass(frozen=True)
class FeedRecord:
    source_name: str
    source_kind: str
    title: str
    url: str
    summary: str
    observed_at: str
    price_pence: int | None = None
    supplier_evidence: dict[str, object] | None = None


@dataclass(frozen=True)
class SourceCollection:
    fetched_at: str
    records: tuple[FeedRecord, ...]
    source_errors: dict[str, str]
    sources_configured: int
    sources_succeeded: int


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_https(
    url: str,
    *,
    allowed_hosts: tuple[str, ...],
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_bytes: int = MAX_RESPONSE_BYTES,
) -> tuple[bytes, str]:
    """Fetch a bounded HTTPS response from one allowlisted host without redirects."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("only HTTPS source URLs are allowed")
    if parsed.hostname.lower().rstrip(".") not in {
        host.lower().rstrip(".") for host in allowed_hosts
    }:
        raise ValueError("source host is not allowlisted")
    if max_bytes < 1 or timeout <= 0:
        raise ValueError("response limit and timeout must be positive")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/json, application/xml"})
    opener = build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.geturl() != url:
                raise ValueError("redirects are not accepted")
            content_type = response.headers.get_content_type()
            body = response.read(max_bytes + 1)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP source error: {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"source request failed: {type(exc).__name__}") from exc
    if len(body) > max_bytes:
        raise ValueError("source response exceeded the configured size limit")
    return body, content_type


def _safe_record_url(value: str, source: SourceDefinition) -> str:
    parsed = urlparse(value)
    allowed = {host.lower().rstrip(".") for host in source.allowed_hosts}
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("feed record URL must use HTTPS")
    if parsed.hostname.lower().rstrip(".") not in allowed:
        raise ValueError("feed record host is not allowlisted")
    return value


def _parse_rss(body: bytes, source: SourceDefinition, fetched_at: str) -> list[FeedRecord]:
    root = ET.fromstring(body)
    records: list[FeedRecord] = []
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    for item in items[:source.max_records]:
        title = (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link = (item.findtext("link") or "").strip()
        if not link:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            link = atom_link.attrib.get("href", "") if atom_link is not None else ""
        summary = (
            item.findtext("description")
            or item.findtext("{http://www.w3.org/2005/Atom}summary")
            or ""
        ).strip()
        if not title or not link:
            continue
        records.append(FeedRecord(
            source_name=source.name,
            source_kind=source.kind,
            title=title[:300],
            url=_safe_record_url(link, source),
            summary=re.sub(r"<[^>]*>", " ", summary)[:2000],
            observed_at=fetched_at,
        ))
    return records


def _parse_supplier_json(body: bytes, source: SourceDefinition, fetched_at: str) -> list[FeedRecord]:
    payload = json.loads(body.decode("utf-8"))
    items = payload.get("offers") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        raise TypeError("supplier JSON must contain an offers array")
    records: list[FeedRecord] = []
    for item in items[:source.max_records]:
        if not isinstance(item, dict):
            continue
        title = item.get("title")
        url = item.get("url")
        if not isinstance(title, str) or not title.strip() or not isinstance(url, str):
            continue
        price = item.get("price_pence")
        if price is not None and (type(price) is not int or price < 0):
            raise ValueError("supplier price_pence must be a non-negative integer")
        evidence_keys = (
            "stock_status", "stock_checked_at", "unit_cost_pence",
            "shipping_cost_pence", "ships_to_uk", "delivery_days_min",
            "delivery_days_max", "returns_policy_url", "evidence_excerpt",
            "evidence_checked_at",
        )
        evidence = {key: item[key] for key in evidence_keys if key in item}
        if "returns_policy_url" in evidence:
            evidence["returns_policy_url"] = _safe_record_url(
                str(evidence["returns_policy_url"]), source
            )
        records.append(FeedRecord(
            source_name=source.name,
            source_kind=source.kind,
            title=title.strip()[:300],
            url=_safe_record_url(url, source),
            summary="Supplier-provided structured offer evidence; not independently audited.",
            observed_at=fetched_at,
            price_pence=price,
            supplier_evidence=evidence,
        ))
    return records


def collect_sources(
    sources: tuple[SourceDefinition, ...] | list[SourceDefinition],
    *,
    fetcher: Callable[..., tuple[bytes, str]] = fetch_https,
    now: datetime | None = None,
) -> SourceCollection:
    """Collect configured feeds independently; failures are explicit per source."""
    checked_at = now or datetime.now(UTC)
    if checked_at.tzinfo is None or checked_at.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    fetched_at = checked_at.isoformat()
    records: list[FeedRecord] = []
    errors: dict[str, str] = {}
    succeeded = 0
    selected = [source for source in sources if source.enabled]
    for source in selected:
        try:
            body, content_type = fetcher(source.url, allowed_hosts=source.allowed_hosts)
            if source.kind == "supplier_json":
                if content_type not in {"application/json", "text/json"}:
                    raise ValueError("supplier source must return JSON content")
                records.extend(_parse_supplier_json(body, source, fetched_at))
            else:
                if content_type not in {"application/rss+xml", "application/atom+xml", "application/xml", "text/xml"}:
                    raise ValueError("product and demand feeds must return XML content")
                records.extend(_parse_rss(body, source, fetched_at))
            succeeded += 1
        except (RuntimeError, ValueError, ET.ParseError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors[source.name] = f"{type(exc).__name__}: {exc}"
    return SourceCollection(
        fetched_at=fetched_at,
        records=tuple(records),
        source_errors=errors,
        sources_configured=len(selected),
        sources_succeeded=succeeded,
    )


def collection_to_dict(result: SourceCollection) -> dict:
    """Return JSON-ready records with explicit evidence limitations."""
    return {
        "fetched_at": result.fetched_at,
        "records": [asdict(record) for record in result.records],
        "source_errors": result.source_errors,
        "sources_configured": result.sources_configured,
        "sources_succeeded": result.sources_succeeded,
        "limitations": [
            "Feed records are leads, not verified sales demand.",
            "Product feed records do not establish stock or supplier availability.",
            "Supplier feed records are claims from the configured source, not independent audits.",
            "No records are published, purchased or sent to customers.",
        ],
    }
