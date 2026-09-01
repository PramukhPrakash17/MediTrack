import shutil
import uuid
from pathlib import Path

from app.config.settings import settings


class SessionManager:
    """Tracks exactly one active consultation at a time.

    The doctor never sees or passes an id: this holds the single "current"
    consultation_id server-side and hands it to the graph as the LangGraph
    thread_id. /new-patient replaces it; /chat always operates on whichever
    one is current. This assumes a single doctor / single browser tab talking
    to this backend at a time - it is not safe for concurrent consultations.
    """

    def __init__(self):
        self._current_id: str | None = None
        self._base_dir = Path(settings.temp_upload_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def current_consultation_id(self) -> str:
        if self._current_id is None:
            self._current_id = str(uuid.uuid4())
        return self._current_id

    def start_new_consultation(self) -> str:
        self._clear_uploads(self._current_id)
        self._current_id = str(uuid.uuid4())
        return self._current_id

    def save_upload(self, filename: str, content: bytes) -> Path:
        consultation_dir = self._base_dir / self.current_consultation_id()
        consultation_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(filename).suffix.lower()
        # Generic name: this holds either an X-ray image or a lab-report
        # document now, decided later by which tool the agent calls.
        temp_path = consultation_dir / f"upload{suffix}"
        temp_path.write_bytes(content)
        # The X-ray MCP tool runs as a separate process with its own working
        # directory, so a relative path here would resolve against the wrong
        # cwd there. Must be absolute.
        return temp_path.resolve()

    def _clear_uploads(self, consultation_id: str | None) -> None:
        if consultation_id is None:
            return
        upload_dir = self._base_dir / consultation_id
        shutil.rmtree(upload_dir, ignore_errors=True)
