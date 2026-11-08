from ultron.github_queue import GitHubQueue


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
