from ultron.github_queue import GitHubAPIError, GitHubQueue


def test_issue_queue_ignores_untrusted_authors_and_pull_requests():
    queue = GitHubQueue("token", "owner/repo")
    queue._request = lambda method, path: [
        {"number": 1, "author_association": "OWNER"},
        {"number": 2, "author_association": "CONTRIBUTOR"},
        {"number": 3, "author_association": "COLLABORATOR", "pull_request": {}},
        {"number": 4, "author_association": "MEMBER"},
    ]
    issues = queue.list_issues("FINANCE", "ready")
    assert [issue["number"] for issue in issues] == [1, 4]


def test_issue_queue_reads_later_pages_and_filters_each_page():
    queue = GitHubQueue("token", "owner/repo")
    first = [{"number": n, "author_association": "OWNER"} for n in range(1, 101)]
    second = [
        {"number": 101, "author_association": "MEMBER"},
        {"number": 102, "author_association": "CONTRIBUTOR"},
        {"number": 103, "author_association": "COLLABORATOR", "pull_request": {}},
    ]
    requested = []

    def request(method, path):
        requested.append(path)
        return first if "page=1" in path else second

    queue._request = request
    issues = queue.list_issues("FINANCE", "ready")

    assert [issue["number"] for issue in issues][-1] == 101
    assert len(issues) == 101
    assert len(requested) == 2
    assert "page=1" in requested[0]
    assert "page=2" in requested[1]


def test_issue_queue_fails_closed_when_later_page_fails():
    queue = GitHubQueue("token", "owner/repo")
    first = [{"number": n, "author_association": "OWNER"} for n in range(1, 101)]

    def request(method, path):
        if "page=1" in path:
            return first
        raise GitHubAPIError("page two unavailable")

    queue._request = request
    try:
        queue.list_issues("FINANCE", "ready")
    except GitHubAPIError as exc:
        assert "page two unavailable" in str(exc)
    else:
        raise AssertionError("later-page failure must not return a truncated queue")


def test_comments_reads_all_pages_without_duplicates():
    queue = GitHubQueue("token", "owner/repo")
    first = [{"id": n, "body": f"comment-{n}"} for n in range(1, 101)]
    second = [{"id": 101, "body": "comment-101"}]
    requested = []

    def request(method, path):
        requested.append(path)
        return first if "page=1" in path else second

    queue._request = request
    comments = queue.comments(42)

    assert len(comments) == 101
    assert len({comment["id"] for comment in comments}) == 101
    assert len(requested) == 2
