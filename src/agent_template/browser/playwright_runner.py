from __future__ import annotations

from playwright.sync_api import Browser, Page, sync_playwright

from ..config import Config
from ..models import ArtifactRef
from ..runtime.artifact_store import ArtifactStore

cfg = Config()


class PlaywrightRunner:
    """Thin wrapper around Playwright for deterministic browser checks."""

    def __init__(self, artifact_store: ArtifactStore, run_id: str) -> None:
        self.artifact_store = artifact_store
        self.run_id = run_id
        self._pw = None
        self._browser: Browser | None = None
        self._page: Page | None = None
        self._console_errors: list[str] = []
        self._network_failures: list[str] = []

    def start(self, headless: bool = True) -> None:
        """Start the Playwright browser and create a new page."""
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        context = self._browser.new_context(viewport={**cfg.viewport_size})
        self._page = context.new_page()
        self.set_handlers()

    def _on_console(self, msg) -> None:
        if msg.type == 'error':
            self._console_errors.append(msg.text)

    def _on_request_failed(self, req) -> None:
        self._network_failures.append(f'{req.method} {req.url} failed')

    def set_handlers(self) -> None:
        self._page.on('console', self._on_console)
        self._page.on('requestfailed', self._on_request_failed)

    def _validate_browser_started(self) -> bool:
        if self._browser is None or self._page is None:
            raise RuntimeError('Browser not started.')
        return True

    @property
    def page(self) -> Page:
        if self._validate_browser_started():
            return self._page
        raise RuntimeError('Browser not started.')

    def goto(self, url: str) -> None:
        self.page.goto(url, wait_until='networkidle')

    def screenshot(self, label: str) -> ArtifactRef:
        self._validate_browser_started()
        path = self.artifact_store.run_path(self.run_id, f'screenshot/{label}.png')
        self.page.screenshot(path=path, full_page=True)
        return ArtifactRef(kind='screenshot', path=str(path), label=label)

    def dom_snapshot(self, label: str) -> ArtifactRef:
        self._validate_browser_started()
        return self.artifact_store.write_run_text(
            self.run_id,
            f'dom_snapshot/{label}.html',
            self.page.content(),
            kind='dom_snapshot',
            label=label,
        )

    def console_errors(self) -> list[str]:
        return list(self._console_errors)

    def network_failures(self) -> list[str]:
        return list(self._network_failures)

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._pw is not None:
            self._pw.stop()
