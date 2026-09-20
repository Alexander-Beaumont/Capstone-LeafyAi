VALID_ENTRY = {
    "created_at": "2026-09-06T10:30:00Z",
    "entry_id": 12345,
    "field1": "6.12",
    "field2": "1480",
    "field3": "21.3",
    "field4": "24.6",
    "field5": "64.1",
    "field6": "18.2",
    "field7": "1",
    "field8": "1500",
}


def make_entry(entry_id, created_at, **overrides):
    payload = dict(VALID_ENTRY)
    payload["entry_id"] = entry_id
    payload["created_at"] = created_at
    payload.update(overrides)
    return payload
