import pytest

from ultron.assets import RegistryError, counts, record_asset, record_opportunity


def test_asset_requires_evidence_and_payment_ref_for_revenue(tmp_path):
    db = str(tmp_path / "a.db")
    with pytest.raises(RegistryError):
        record_asset(
            db,
            asset_id="x",
            name="x",
            category="repository",
            platform="github",
            access_evidence="",
            url="https://github.com/cloyboy0904360-ai/Ultron",
            status="VERIFIED",
            next_action="none",
        )
    with pytest.raises(RegistryError):
        record_asset(
            db,
            asset_id="x",
            name="x",
            category="repository",
            platform="github",
            access_evidence="gh repo list",
            url="https://github.com/cloyboy0904360-ai/Ultron",
            status="VERIFIED",
            next_action="none",
            revenue_cents=100,
        )
    record_asset(
        db,
        asset_id="github:Ultron",
        name="Ultron",
        category="repository",
        platform="github",
        access_evidence="gh repo list",
        url="https://github.com/cloyboy0904360-ai/Ultron",
        status="VERIFIED",
        next_action="keep as controller repository",
    )
    assert counts(db)["verified_assets"] == 1


def test_opportunity_without_source_is_rejected(tmp_path):
    db = str(tmp_path / "a.db")
    with pytest.raises(RegistryError):
        record_opportunity(
            db,
            name="idea",
            source_url="",
            demand_evidence="none",
            risks="unknown",
            next_action="stop",
        )
    with pytest.raises(RegistryError):
        record_opportunity(
            db,
            name="priced",
            source_url="https://example.com/source",
            demand_evidence="page lists a price",
            risks="unverified",
            next_action="do not sell",
            status="VERIFIED",
        )
