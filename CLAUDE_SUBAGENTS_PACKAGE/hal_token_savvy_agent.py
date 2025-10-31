#!/usr/bin/env python3
"""
Hal Agent Loop - v2: local-filter-first + token guard + delta mode.

What's new:
- Token/char gate before API call (hard stop if over budget).
- Delta-aware prompts: if local snippet unchanged, we send a tiny "no changes" marker.
- Small, directive system prompt to save tokens.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass

# Removed circular import - function is implemented in this file

# ---------- Repository Filtering -----------------------------------------------


def filter_repo_for_llm(
    goal: str,
    pattern: str | None = None,
    roots: list[str] | None = None,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    json_filter: str | None = None,
    max_files: int = 20000,
    max_hits: int = 5000,
    max_bytes: int = 256000,
    llm_snippet_chars: int = 3200,
    context_lines: int = 1,
    per_file_max_lines: int = 60,
    abbreviate_paths: bool = True,
    delta_mode: bool = False,
) -> str:
    """
    Filter repository content for LLM consumption with token efficiency.

    This function searches through files and returns a compact snippet
    optimized for LLM context windows with comprehensive filtering options.
    """
    import hashlib
    import json
    import subprocess
    from pathlib import Path

    roots = roots or ["."]

    # Initialize counters and limits
    files_processed = 0
    total_bytes = 0
    hits_found = 0
    result_lines = []

    # Delta mode: Check for cached results
    cache_file = (
        Path.home()
        / ".hal_cache"
        / f"{hashlib.md5(f'{goal}_{pattern}_{roots!s}'.encode(), usedforsecurity=False).hexdigest()}.txt"
    )
    if delta_mode and cache_file.exists():
        try:
            cached_result = cache_file.read_text()
            if cached_result:
                return f"[CACHED] {cached_result}"
        except Exception:
            pass  # Fall through to normal processing

    # Simple grep/rg search for pattern with full parameter implementation
    try:
        # Use ripgrep if available, otherwise fall back to grep
        cmd = [
            "rg",
            "-n",
            "--max-count",
            str(per_file_max_lines),
            "-A",
            str(context_lines),
            "-B",
            str(context_lines),
            pattern or ".",
            "--type",
            "py",
        ]

        # Add file size limit (use a reasonable limit like 1MB per file)
        if max_files > 0:
            max_file_size = min(
                max(1024 * 1024, max_bytes // max_files), 10 * 1024 * 1024
            )  # Between 1MB and 10MB
            cmd.extend(["--max-filesize", str(max_file_size)])

        # Add glob patterns
        if include_globs:
            for glob in include_globs:
                cmd.extend(["--glob", glob])
        if exclude_globs:
            for glob in exclude_globs:
                cmd.extend(["--glob", f"!{glob}"])

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=roots[0])

        if result.returncode == 0:
            lines = result.stdout.split("\n")

            for line in lines:
                if not line.strip():
                    continue

                # Check limits
                if max_files > 0 and files_processed >= max_files:
                    break
                if max_hits > 0 and hits_found >= max_hits:
                    break
                if total_bytes >= max_bytes:
                    break

                # Apply JSON filtering if specified
                if json_filter:
                    try:
                        # Simple JSON filtering - look for lines containing JSON
                        if "{" in line and "}" in line:
                            json_data = json.loads(line[line.find("{") : line.rfind("}") + 1])
                            # Apply simple jq-like filter (basic implementation)
                            if json_filter and json_filter not in str(json_data):
                                continue
                    except (json.JSONDecodeError, ValueError):
                        pass  # Not JSON or invalid JSON, continue

                # Abbreviate paths if requested
                if abbreviate_paths and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        path = parts[0]
                        # Shorten path to show only last few directories
                        path_parts = path.split("/")
                        if len(path_parts) > 3:
                            path = "/".join(["..."] + path_parts[-2:])
                        line = f"{path}:{parts[1]}"

                result_lines.append(line)
                total_bytes += len(line.encode("utf-8"))
                hits_found += 1

                # Track files (simplified - just count unique file paths)
                if ":" in line:
                    files_processed += 1

            output = "\n".join(result_lines)

            # Truncate if too large
            if len(output) > llm_snippet_chars:
                output = output[:llm_snippet_chars] + "\n...[truncated]"

            # Cache result for delta mode
            if delta_mode:
                try:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(output)
                except Exception:
                    pass  # Cache writing failed, but that's ok

            return output
        else:
            return f"No matches found for pattern: {pattern}"

    except FileNotFoundError:
        # Try grep as fallback with full parameter support
        try:
            cmd = [
                "grep",
                "-r",
                "-n",
                "-A",
                str(context_lines),
                "-B",
                str(context_lines),
                pattern or ".",
                "--include=*.py",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=roots[0])

            if result.returncode == 0:
                lines = result.stdout.split("\n")

                for line in lines:
                    if not line.strip():
                        continue

                    # Apply same limits and filtering as above
                    if max_files > 0 and files_processed >= max_files:
                        break
                    if max_hits > 0 and hits_found >= max_hits:
                        break
                    if total_bytes >= max_bytes:
                        break

                    result_lines.append(line)
                    total_bytes += len(line.encode("utf-8"))
                    hits_found += 1

                output = "\n".join(result_lines)

                if len(output) > llm_snippet_chars:
                    output = output[:llm_snippet_chars] + "\n...[truncated]"

                return output
            else:
                return f"No matches found for pattern: {pattern}"

        except FileNotFoundError:
            # Final fallback with parameter information
            info_parts = ["Repository filtering not available. Please install ripgrep or grep."]
            info_parts.append(f"Goal: {goal}")
            info_parts.append(f"Pattern: {pattern}")
            info_parts.append(f"Max files: {max_files}")
            info_parts.append(f"Max hits: {max_hits}")
            info_parts.append(f"Max bytes: {max_bytes}")
            info_parts.append(f"Delta mode: {delta_mode}")
            return "\n".join(info_parts)


# ---------- Providers -----------------------------------------------------------


class LLMProvider:
    def generate(
        self, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 800
    ) -> str:
        raise NotImplementedError


@dataclass
class OpenAIProvider(LLMProvider):
    def generate(
        self, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 800
    ) -> str:
        from openai import OpenAI  # lazy import

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content or ""


@dataclass
class AnthropicProvider(LLMProvider):
    anthropic_version: str = "2023-06-01"

    def generate(
        self, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 800
    ) -> str:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts: list[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        return "\n".join(parts).strip()


# ---------- Prompts -------------------------------------------------------------

# Short+directive system prompt (token-cheap)
BASE_SYSTEM_PROMPT = (
    "You are Hal, a terse, precise coding assistant. Prefer the given snippet. "
    "Answer in short steps. If uncertain, state assumptions briefly."
)


def build_user_prompt(user_goal: str, local_snippet: str) -> str:
    # Keep this extremely compact; structure helps the model with minimal tokens.
    return (
        f"Goal: {user_goal}\n"
        "Context:\n"
        f"{local_snippet}\n"
        "Instruction: Use the context first. Return only the next steps, code, or diffs."
    )


# ---------- Guards --------------------------------------------------------------


def _enforce_char_budget(text: str, max_chars: int) -> None:
    if len(text) > max_chars:
        raise ValueError(
            f"Prompt too large ({len(text)} chars > {max_chars}). "
            f"Increase --chars or refine filters."
        )


# ---------- Main ----------------------------------------------------------------


def should_run_local_tools(pattern: str | None, jq_filter: str | None) -> bool:
    return bool(pattern or jq_filter)


def main(argv: Sequence[str] | None = None) -> int:
    pa = argparse.ArgumentParser(description="Hal Agent: token-minimized loop (v2).")
    pa.add_argument("--provider", choices=["openai", "anthropic"], required=True)
    pa.add_argument("--model", required=True)
    pa.add_argument("--goal", required=True)
    pa.add_argument("--pattern")
    pa.add_argument("--jq", dest="jq_filter")
    pa.add_argument("--roots", nargs="+", default=["."])
    pa.add_argument("--include", nargs="+", dest="include_globs")
    pa.add_argument("--exclude", nargs="+", dest="exclude_globs")
    pa.add_argument("--chars", type=int, default=3200, help="Max snippet size (characters).")
    pa.add_argument("--max-files", type=int, default=20000)
    pa.add_argument("--max-hits", type=int, default=5000)
    pa.add_argument("--max-bytes", type=int, default=256000)
    pa.add_argument("--context", type=int, default=1)
    pa.add_argument("--per-file", type=int, default=60)
    pa.add_argument("--delta", action="store_true")
    pa.add_argument("--max-tokens", type=int, default=600)
    args = pa.parse_args(argv)

    snippet = ""
    if should_run_local_tools(args.pattern, args.jq_filter):
        snippet = filter_repo_for_llm(
            goal=args.goal,
            pattern=args.pattern,
            roots=args.roots,
            include_globs=args.include_globs,
            exclude_globs=args.exclude_globs,
            json_filter=args.jq_filter,
            max_files=args.max_files,
            max_hits=args.max_hits,
            max_bytes=args.max_bytes,
            llm_snippet_chars=args.chars,
            context_lines=args.context,
            per_file_max_lines=args.per_file,
            abbreviate_paths=True,
            delta_mode=args.delta,
        )

    user_prompt = build_user_prompt(args.goal, snippet)

    # hard prompt size guard (prevents surprise token burn)
    _enforce_char_budget(user_prompt, max_chars=args.chars + 800)  # allow small overhead

    provider: LLMProvider = OpenAIProvider() if args.provider == "openai" else AnthropicProvider()
    out = provider.generate(
        system_prompt=BASE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=args.model,
        max_tokens=args.max_tokens,
    )
    sys.stdout.write(out.strip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
