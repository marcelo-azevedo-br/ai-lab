from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from ai_lab.config import FactoryConfig, WorkerConfig
from ai_lab.shell import ShellRunner


@dataclass(slots=True)
class ToolEvent:
    name: str
    status: str
    summary: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        return " ".join(self.parts)


class ToolRegistry:
    def __init__(self, config: FactoryConfig, shell_runner: ShellRunner) -> None:
        self.config = config
        self.shell_runner = shell_runner

    def build_report(self, worker: WorkerConfig, prompt: str, *, cwd: Path) -> tuple[str, list[ToolEvent]]:
        shared: dict[str, Any] = {}
        events: list[ToolEvent] = []
        for tool_name in worker.tools:
            event = self._run_tool(tool_name, worker=worker, prompt=prompt, cwd=cwd, shared=shared)
            if event is None:
                continue
            events.append(event)
            if tool_name == "brave_search":
                shared["search_results"] = event.metadata.get("results", [])

        lines = [f"# Tool Report - {worker.name}", ""]
        if not events:
            lines.append("- no tools executed")
        for event in events:
            lines.extend(
                [
                    f"## {event.name}",
                    f"- status: {event.status}",
                    f"- summary: {event.summary}",
                    "",
                    event.body.strip() or "_no body_",
                    "",
                ]
            )
        return "\n".join(lines).strip() + "\n", events

    def _run_tool(
        self,
        tool_name: str,
        *,
        worker: WorkerConfig,
        prompt: str,
        cwd: Path,
        shared: dict[str, Any],
    ) -> ToolEvent | None:
        if tool_name == "brave_search":
            return self._run_brave_search(prompt, worker=worker)
        if tool_name == "fetch":
            return self._run_fetch(shared.get("search_results", []))
        if tool_name == "repo_snapshot":
            return self._run_repo_snapshot(cwd)
        if tool_name == "repo_search":
            return self._run_repo_search(prompt, cwd)
        if tool_name == "git_status":
            return self._run_git_status(cwd)
        return ToolEvent(
            name=tool_name,
            status="skipped",
            summary="unknown tool",
            body=f"Tool `{tool_name}` is not implemented yet.",
        )

    def _run_brave_search(self, prompt: str, *, worker: WorkerConfig) -> ToolEvent:
        cfg = self.config.tools.brave_search
        if not cfg.enabled:
            return ToolEvent("brave_search", "skipped", "disabled in config", "Brave Search is disabled.")

        api_key = os.getenv(cfg.api_key_env, "").strip()
        if not api_key:
            return ToolEvent(
                "brave_search",
                "skipped",
                f"missing env {cfg.api_key_env}",
                f"Set `{cfg.api_key_env}` to enable live web research for `{worker.name}`.",
            )

        queries = self._derive_search_queries(prompt, worker.name)
        all_results: list[dict[str, str]] = []
        query_sections: list[str] = []
        for query in queries:
            try:
                results = self._brave_search(query, api_key=api_key)
            except Exception as exc:  # pragma: no cover - network path
                query_sections.append(f"### query: {query}\n- error: {exc}\n")
                continue

            query_sections.append(f"### query: {query}")
            if not results:
                query_sections.append("- no results\n")
                continue
            for result in results[: max(1, cfg.count // 2)]:
                all_results.append(result)
                query_sections.append(
                    f"- [{result['title']}]({result['url']})\n  - {result['description']}"
                )
            query_sections.append("")

        deduped: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for result in all_results:
            url = result.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deduped.append(result)
            if len(deduped) >= cfg.count:
                break

        summary = f"{len(deduped)} results from {len(queries)} queries"
        return ToolEvent(
            name="brave_search",
            status="ok",
            summary=summary,
            body="\n".join(query_sections).strip() or "_no results_",
            metadata={"results": deduped},
        )

    def _run_fetch(self, search_results: list[dict[str, str]]) -> ToolEvent:
        cfg = self.config.tools.fetch
        if not cfg.enabled:
            return ToolEvent("fetch", "skipped", "disabled in config", "HTTP fetch is disabled.")
        if not search_results:
            return ToolEvent("fetch", "skipped", "no URLs from previous tool", "No URLs available to fetch.")

        bodies: list[str] = []
        fetched = 0
        for result in search_results[: cfg.max_pages]:
            url = result.get("url", "")
            if not url:
                continue
            try:
                text = self._fetch_url_text(url)
            except Exception as exc:  # pragma: no cover - network path
                bodies.append(f"### {url}\n- error: {exc}\n")
                continue
            fetched += 1
            snippet = text[: cfg.max_chars].strip()
            bodies.append(
                f"### {result.get('title') or url}\n- url: {url}\n- domain: {urlparse(url).netloc}\n\n{snippet}\n"
            )

        return ToolEvent(
            name="fetch",
            status="ok" if fetched else "skipped",
            summary=f"{fetched} pages fetched",
            body="\n".join(bodies).strip() or "_no pages fetched_",
        )

    def _run_repo_snapshot(self, cwd: Path) -> ToolEvent:
        cfg = self.config.tools.repo
        if not cfg.enabled:
            return ToolEvent("repo_snapshot", "skipped", "disabled in config", "Repo tools are disabled.")

        if shutil.which("rg"):
            files_result = self.shell_runner.run(["rg", "--files"], cwd=cwd, allow_failure=True)
            files = [line for line in files_result.stdout.splitlines() if line.strip()]
        else:
            files = [
                str(path.relative_to(cwd))
                for path in cwd.rglob("*")
                if path.is_file()
            ]
        clipped_files = files[: cfg.max_files]
        lines = ["### files", *[f"- {path}" for path in clipped_files]]
        summary = f"{len(clipped_files)} files listed"
        if len(files) > len(clipped_files):
            lines.append(f"- ... clipped from {len(files)} total files")
        return ToolEvent("repo_snapshot", "ok", summary, "\n".join(lines))

    def _run_repo_search(self, prompt: str, cwd: Path) -> ToolEvent:
        cfg = self.config.tools.repo
        if not cfg.enabled:
            return ToolEvent("repo_search", "skipped", "disabled in config", "Repo tools are disabled.")
        if not shutil.which("rg"):
            return ToolEvent("repo_search", "skipped", "rg not available", "Install `rg` to enable repo search.")

        keywords = self._derive_repo_keywords(prompt)
        bodies: list[str] = []
        hits = 0
        for keyword in keywords:
            result = self.shell_runner.run(
                ["rg", "-n", "--max-count", "8", keyword, "."],
                cwd=cwd,
                allow_failure=True,
            )
            matches = [line for line in result.stdout.splitlines() if line.strip()][: cfg.max_matches]
            if not matches:
                continue
            hits += len(matches)
            bodies.append(f"### keyword: {keyword}")
            bodies.extend([f"- {line}" for line in matches])
            bodies.append("")

        if not bodies:
            return ToolEvent("repo_search", "skipped", "no useful matches", "No repository matches found.")
        return ToolEvent("repo_search", "ok", f"{hits} matches across {len(keywords)} keywords", "\n".join(bodies).strip())

    def _run_git_status(self, cwd: Path) -> ToolEvent:
        result = self.shell_runner.run(["git", "status", "--short"], cwd=cwd, allow_failure=True)
        if result.returncode != 0:
            body = result.stderr.strip() or "git status failed"
            return ToolEvent("git_status", "skipped", "git status unavailable", body)
        body = result.stdout.strip() or "working tree clean"
        return ToolEvent("git_status", "ok", "captured git working tree status", body)

    def _brave_search(self, query: str, *, api_key: str) -> list[dict[str, str]]:
        cfg = self.config.tools.brave_search
        params = urlencode(
            {
                "q": query,
                "count": cfg.count,
                "country": cfg.country,
                "search_lang": cfg.search_lang,
                "ui_lang": cfg.ui_lang,
            }
        )
        request = Request(
            f"{cfg.endpoint}?{params}",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": api_key,
                "User-Agent": self.config.tools.fetch.user_agent,
            },
        )
        with urlopen(request, timeout=self.config.tools.fetch.timeout_seconds) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))

        raw_results = payload.get("web", {}).get("results", [])
        results: list[dict[str, str]] = []
        for item in raw_results:
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            description = str(item.get("description", "")).strip()
            if title and url:
                results.append({"title": title, "url": url, "description": description})
        return results

    def _fetch_url_text(self, url: str) -> str:
        cfg = self.config.tools.fetch
        request = Request(url, headers={"User-Agent": cfg.user_agent})
        with urlopen(request, timeout=cfg.timeout_seconds) as response:  # noqa: S310
            raw = response.read(cfg.max_chars * 4).decode("utf-8", errors="replace")

        parser = _HTMLTextExtractor()
        parser.feed(raw)
        text = parser.text()
        text = re.sub(r"\s+", " ", text).strip()
        return text[: cfg.max_chars]

    def _derive_search_queries(self, prompt: str, worker_name: str) -> list[str]:
        fields = self._prompt_fields(prompt)
        vertical = fields.get("vertical", "").strip()
        objective = fields.get("objetivo", "").strip() or fields.get("objective", "").strip()
        context = fields.get("contexto adicional", "").strip() or fields.get("context", "").strip()

        base = vertical or objective or "software vertical"
        queries = [
            f"{base} whatsapp atendimento",
            f"{base} software despacho",
            f"{base} concorrentes app",
        ]
        if objective:
            queries.append(f"{base} {objective}")
        if context:
            queries.append(f"{base} {context}")
        if worker_name == "marketing":
            queries.append(f"{base} anuncios google")
        return self._unique(queries)[:3]

    def _derive_repo_keywords(self, prompt: str) -> list[str]:
        fields = self._prompt_fields(prompt)
        candidates = [
            fields.get("vertical", ""),
            fields.get("approved_idea", ""),
            fields.get("objective", ""),
            fields.get("objetivo", ""),
        ]
        tokens: list[str] = []
        for candidate in candidates:
            for token in re.split(r"[^a-zA-Z0-9]+", candidate.lower()):
                if len(token) >= 4:
                    tokens.append(token)
        defaults = ["guincho", "whatsapp", "mvp", "landing", "build"]
        return self._unique(tokens + defaults)[:5]

    def _prompt_fields(self, prompt: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for line in prompt.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip()
        return fields

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            result.append(normalized)
        return result
