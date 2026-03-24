<!-- markdownlint-disable MD024 -->
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.3.0] - 2026-03-24

### Added

- A first local discovery prototype for interrupted-task memory evaluation.
- A small `memoryvault/` package with local run storage, candidate memory extraction, resume packet generation, and evaluation logging.
- Built-in sample scenarios for coding and document work.
- A JSON intake path for imported interrupted-task traces.
- Example imported traces modeled after coding and long-memory work.
- A synthetic tool-use trace for domain-agnostic interrupted-task testing.
- A Hugging Face benchmark lead registry for later external evaluation.
- A durable-field suggestion step that highlights repeated misses.
- Automated tests covering the local discovery loop.
- A strategy note describing the tool-first, zero-domain-knowledge development phases.
- A Memory Wind Tunnel that removes memory fields and measures the damage.
- A repo-local quality gate with a pre-commit hook, Python linting, Markdown linting, and a 90% coverage threshold.

### Changed

- Replaced the placeholder root entry point with a working CLI.
- Promoted `assumptions` into the resume packet after repeated misses across scenarios.
- Reframed the project from a domain-specific product direction to a tool-first memory-learning direction.
- Updated project docs and `.codex` notes to reflect the new prototype state.

## [0.2.0] - 2026-03-24

### Added

- Repo-local project memory in `.codex/` for status, planning, decisions, research, and maintenance notes.
- A root `AGENTS.md` file that tells future sessions how to read and maintain the project memory.
- A product brief in `docs/PRD.md`.
- A research summary in `docs/research.md`.
- A root changelog in `Chaneglog.md`.

### Changed

- Renamed the project from `Pensieve` to `MemoryVault` locally and on GitHub.
- Reworked `README.md` into a short GitHub-friendly project overview.
- Updated project metadata in `pyproject.toml` to match the new name and current purpose.
- Updated the placeholder entry point to use the new project name.
