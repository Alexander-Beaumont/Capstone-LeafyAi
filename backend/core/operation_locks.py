import threading


_registry_guard = threading.Lock()
_locks = {}


def operation_lock(kind, object_id):
    key = (kind, int(object_id))
    with _registry_guard:
        return _locks.setdefault(key, threading.Lock())
