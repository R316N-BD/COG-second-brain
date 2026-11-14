"""Run only allowlisted maintenance operations, with persisted job outcomes."""
from . import memory, operations
from .paths import private_path

def run(data_dir, action):
    root = private_path(data_dir)
    if action not in {"index-refresh"}:
        raise ValueError("Unknown maintenance action.")
    job = operations.create_job(root, action, "local-maintenance")
    ident = job["id"]
    operations.job_transition(root, ident, "running")
    try:
        result = memory.rebuild(root, incremental=True)
    except BaseException:
        operations.job_transition(root, ident, "failed")
        raise
    operations.job_transition(root, ident, "completed")
    return {"job": ident, "status": "completed", "result": result}
