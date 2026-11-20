from ultron.github_queue import GitHubQueue


def test_issue_queue_ignores_untrusted_authors_and_pull_requests():
    queue = GitHubQueue("token", "owner/repo")
    queue._request = lambda method, path: [
        {
            "number": 1,
            "author_association": "OWNER",
            "labels": [{"name": "agent:finance"}, {"name": "status:ready"}],
        },
        {
            "number": 2,
            "author_association": "CONTRIBUTOR",
            "labels": [{"name": "agent:finance"}, {"name": "status:ready"}],
        },
        {
            "number": 3,
            "author_association": "COLLABORATOR",
            "pull_request": {},
            "labels": [{"name": "agent:finance"}, {"name": "status:ready"}],
        },
        {
            "number": 4,
            "author_association": "MEMBER",
            "labels": [{"name": "agent:finance"}, {"name": "status:ready"}],
        },
    ]
    issues = queue.list_issues("FINANCE", "ready")
    assert [issue["number"] for issue in issues] == [1, 4]


def test_issue_queue_rejects_issues_with_multiple_agent_labels():
    queue = GitHubQueue("token", "owner/repo")
    queue._request = lambda method, path: [
        {
            "number": 10,
            "author_association": "OWNER",
            "labels": [{"name": "agent:finance"}, {"name": "status:ready"}],
        },
        {
            "number": 11,
            "author_association": "OWNER",
            "labels": [
                {"name": "agent:finance"},
                {"name": "agent:sales"},
                {"name": "status:ready"},
            ],
        },
    ]

    issues = queue.list_issues("FINANCE", "ready")

    assert [issue["number"] for issue in issues] == [10]
