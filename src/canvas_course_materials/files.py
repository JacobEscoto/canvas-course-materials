def fetch_file_info(client, course_id: int, file_id: int) -> dict | None:
    response = client.get(f"/courses/{course_id}/files/{file_id}")
    if response.status_code in (403, 404):
        return None
    response.raise_for_status()
    data = response.json()

    return {
        "id": data["id"],
        "filename": data.get("display_name") or data["filename"],
        "url": data["url"],
        "updated_at": data["updated_at"],
    }
