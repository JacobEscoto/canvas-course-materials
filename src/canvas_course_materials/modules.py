def list_module_file_ids(client, course_id: int) -> list[int]:
    seen: set[int] = set()
    ids: list[int] = []

    modules = client.get_paginated(
        f"/courses/{course_id}/modules",
        {"include[]": "items", "per_page": 100},
    )
    for module in modules:
        items = module.get("items")

        if items is None or len(items) < module.get("items_count", 0):
            items = client.get_paginated(
                f"/courses/{course_id}/modules/{module['id']}/items",
                {"per_page": 100},
            )

        for item in items:
            file_id = item.get("content_id")
            if item.get("type") == "File" and file_id not in seen:
                seen.add(file_id)
                ids.append(file_id)
    return ids
