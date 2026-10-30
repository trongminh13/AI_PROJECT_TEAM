# HouseAssist Agent Instructions

## Hoai's project focus

- Hoai's assigned area is the Machine Learning algorithms and related problem-solving tasks in HouseAssist.
- Prioritize understanding, explaining, implementing, and validating the project's Random Forest house-price prediction, K-Means market segmentation, and similar-house search, using the existing King County dataset and project code as the source of truth.
- For algorithm or exercise questions, explain the approach and reasoning clearly before or alongside code. Do not assume Hoai owns unrelated UI, deployment, or repository-wide work unless asked.

## Git workflow

- Make project changes on `features/hoai`; do not commit project work directly to `dev` or `main`.
- Before changing branches, inspect the repository root, current branch, and working tree. Preserve pre-existing or user changes; do not overwrite, discard, or include them in a commit.
- Start from the latest `origin/dev`. If the local `dev` branch is missing, create it tracking `origin/dev`; otherwise fetch and fast-forward it. Create `features/hoai` from `dev` if it does not exist.
- If `features/hoai` already exists, keep working on it and merge the latest `origin/dev` into it before coding. Do not reset or force-push. If the working tree is not clean, or a merge has conflicts, stop and explain rather than risking user changes.
- For follow-up work after a PR has merged, first fetch and fast-forward local `dev`, then merge `origin/dev` into `features/hoai`. Confirm there is a new task change before opening another PR; never create a duplicate or empty PR.
- Keep each task's changes focused. Run relevant project tests and inspect the staged diff before committing. Stage only files changed for the task.
- When the requested work is complete and tests pass, commit the task changes, fetch `origin`, merge the latest `origin/dev` into `features/hoai`, resolve only straightforward conflicts, rerun relevant tests, and push with `git push -u origin features/hoai` (or a normal push if upstream is already configured).
- Create or update a Pull Request with base `dev` and head `features/hoai`. Include a concise summary and test results. Never merge the PR unless the user explicitly asks.
- Use available authenticated GitHub tooling to create the PR. If PR creation is unavailable or authentication/permissions fail, do not claim it succeeded; report the pushed branch and provide this URL for creating it manually: `https://github.com/trongminh13/AI_PROJECT_TEAM/compare/dev...features/hoai?expand=1`.
- Never print, commit, or expose credentials. Do not force-push, rewrite shared history, or discard changes.

## Project checks

- The project is a Python/Streamlit application. Run focused tests for the code changed; the tool suite is `python -X utf8 -m unittest tests/test_tools.py` on Windows.
- Report test failures and unavailable GitHub operations explicitly.
