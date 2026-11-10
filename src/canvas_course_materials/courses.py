def list_active_courses(client) -> list[dict]:
    params = {"enrollment_state": "active", "per_page": 100}
    return [
        course
        for course in client.get_paginated("/users/self/courses", params)
        if "name" in course
    ]
