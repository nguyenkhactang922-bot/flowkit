"""Fast IMP-103 scale contract tests; the measured benchmark lives under tests/performance."""

from collections import Counter

from agent.studio import SchedulerRepository


def test_300_ready_rows_round_robin_three_projects_without_starvation() -> None:
    projects = ("project:a", "project:b", "project:c")
    rows = [
        {
            "generation_job_id": f"job:{project.split(':')[1]}-{index:03d}",
            "priority_class": 10,
            "ready_since": "2026-10-14T00:00:00+00:00",
            "project_id": project,
        }
        for index in range(100)
        for project in projects
    ]

    ordered = SchedulerRepository._fair_order_rows(rows, {10: "project:a"})
    actual_projects = [
        f"project:{job.root.split(':')[1].split('-')[0]}"
        for job in ordered
    ]

    assert len(ordered) == 300
    assert len(set(ordered)) == 300
    assert Counter(actual_projects) == Counter({project: 100 for project in projects})
    assert actual_projects[:9] == ["project:b", "project:c", "project:a"] * 3

    for project in projects:
        positions = [
            index for index, actual in enumerate(actual_projects)
            if actual == project
        ]
        assert max(right - left for left, right in zip(positions, positions[1:])) == 3
