"""SSE progress event emitter for long-running tasks."""

import asyncio
import json
from typing import AsyncGenerator, Optional


class ProgressEmitter:
    """Manages progress events for a single job."""

    def __init__(self, job_id: str, total_steps: int = 4):
        self.job_id = job_id
        self.total_steps = total_steps
        self._queue: asyncio.Queue = asyncio.Queue()
        self._done = False

    async def emit(
        self,
        step: str,
        step_index: int,
        progress: float,
        message: str,
        result: Optional[dict] = None,
        error: Optional[dict] = None,
    ) -> None:
        event = {
            "step": step,
            "step_index": step_index,
            "total_steps": self.total_steps,
            "progress": progress,
            "message": message,
        }
        if result:
            event["result"] = result
        if error:
            event["error"] = error
        await self._queue.put(event)

    async def emit_batch(
        self,
        event_type: str,
        item_index: Optional[int] = None,
        total: Optional[int] = None,
        **kwargs,
    ) -> None:
        event = {"type": event_type}
        if item_index is not None:
            event["item_index"] = item_index
        if total is not None:
            event["total"] = total
        event.update(kwargs)
        await self._queue.put(event)

    async def complete(self) -> None:
        self._done = True
        await self._queue.put(None)  # Sentinel

    async def events(self) -> AsyncGenerator[str, None]:
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield json.dumps(event, ensure_ascii=False)


class JobManager:
    """Manages all active jobs and their progress emitters."""

    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._emitters: dict[str, ProgressEmitter] = {}

    def create_job(self, job_id: str, total_steps: int = 4) -> ProgressEmitter:
        emitter = ProgressEmitter(job_id, total_steps)
        self._jobs[job_id] = {
            "status": "pending",
            "current_step": "",
            "step_index": 0,
            "total_steps": total_steps,
            "progress": 0.0,
        }
        self._emitters[job_id] = emitter
        return emitter

    def get_emitter(self, job_id: str) -> Optional[ProgressEmitter]:
        return self._emitters.get(job_id)

    def get_state(self, job_id: str) -> Optional[dict]:
        state = self._jobs.get(job_id)
        if state:
            return {"job_id": job_id, **state}
        return None

    def update_state(self, job_id: str, **kwargs) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    def remove_job(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
        self._emitters.pop(job_id, None)


# Global singleton
job_manager = JobManager()
