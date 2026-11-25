# Assignment 4: Titlecase Preview Testing Handoff

Prepared for Rami, 25 November 2026. Branch: `a4/matthew-preview-mode`.

## Scope and test locations

Matthew's feature is track preview mode: `beet titlecase -p [QUERY]`.
`--preview` is an equivalent option. Both flags belong **after** `titlecase`:
Beets already uses the global `-p` option to choose plugins.

- New executable tests: `test/plugins/test_titlecase_preview.py` (18 test
  methods, expanded by pytest into 38 cases).
- Existing plugin regressions: `test/plugins/test_titlecase.py` (12 cases,
  unchanged).
- Additional regressions executed: `test/ui/commands/test_modify.py` (39 cases)
  and `test/ui/test_ui_init.py` (4 cases).
- User documentation: `docs/plugins/titlecase.rst`, Running Manually.

The new tests use pytest and the repository's `PluginTestHelper`. Each case gets
isolated configuration and a temporary library. Audio tests copy the repository's
MP3 fixture into a temporary directory; they do not use personal music files.
Most databases are in memory; one case deliberately uses a temporary SQLite file.

## Exact execution commands

Run these PowerShell commands from the repository root. The verified environment
was Windows with Python 3.13.3, pytest 9.1.1, and the existing `.venv`.

New tests only (expected: 38 passed):

```powershell
.\.venv\Scripts\python.exe -m pytest test/plugins/test_titlecase_preview.py -q -o cache_dir=.reports/pytest-cache --junitxml=.reports/a4-preview.xml
```

New and existing titlecase tests (expected: 50 passed):

```powershell
.\.venv\Scripts\python.exe -m pytest test/plugins/test_titlecase_preview.py test/plugins/test_titlecase.py -q -o cache_dir=.reports/pytest-cache --junitxml=.reports/a4-final-titlecase.xml
```

The complete relevant regression selection, including coverage (expected:
93 passed, no failures, errors, or skips):

```powershell
.\.venv\Scripts\python.exe -m pytest test/plugins/test_titlecase_preview.py test/plugins/test_titlecase.py test/ui/commands/test_modify.py test/ui/test_ui_init.py -q -o cache_dir=.reports/pytest-cache --junitxml=.reports/a4-regression.xml --cov=beetsplug.titlecase --cov-report=term-missing --cov-report=xml:.reports/a4-coverage.xml
```

Code and documentation checks:

```powershell
.\.venv\Scripts\ruff.exe check beetsplug/titlecase.py test/plugins/test_titlecase_preview.py
.\.venv\Scripts\ruff.exe format --check beetsplug/titlecase.py test/plugins/test_titlecase_preview.py
.\.venv\Scripts\python.exe -m sphinxlint docs/plugins/titlecase.rst
git diff --check
```

If recreating the environment, the repository's documented setup is `uv sync`.
The test dependency group includes pytest, pytest-cov, and titlecase; documentation
and lint groups supply the checks above. With uv installed, `uv run python -m
pytest` can replace `.\.venv\Scripts\python.exe -m pytest`. Environment creation
was not needed or performed for this implementation.

## Implemented cases and requirement mapping

Requirement numbers below refer to the 13 requested coverage categories in
Task 2. All 38 final cases passed in the executed regression selection.

| Test method | Cases | Requirement(s) | Expected result | Actual result |
| --- | ---: | --- | --- | --- |
| `test_preview_executes_and_shows_original_and_proposed` | 2 | 1, 2 | Both `-p` and `--preview` execute; stdout identifies preview and shows `title: 'in a silent way' -> 'In a Silent Way'`. | 2 passed |
| `test_preview_uses_existing_rules` | 12 | 3, 6, 13 | Correct proposed values for small words, hyphens, parenthesized text, preserved words, preserved phrases, replacements, separators, forced lowercase, first/last small words, artist `The` enabled/disabled, and accented Unicode; stored source field stays unchanged. | 12 passed |
| `test_preview_respects_configured_fields` | 1 | 4 | Only configured artist changes appear; unconfigured title has no change row and remains unchanged. | Passed |
| `test_preview_filters_optional_queries` | 2 | 5 | A title query and a compound artist/year query each display only the selected track. | 2 passed |
| `test_preview_preserves_database_file` | 1 | 6 | A temporary SQLite database has identical bytes and SQL dump before/after; changed proposals are displayed but stored title remains original. | Passed |
| `test_preview_never_calls_persistence_methods` | 1 | 6, 7 | With tag writing enabled, preview calls none of `Item.store`, `Item.try_write`, or `Item.write`. | Passed |
| `test_preview_preserves_music_file_bytes_and_tags` | 1 | 6, 7 | Temporary MP3 bytes, title/artist tags, and stored title remain unchanged with writing enabled. | Passed |
| `test_preview_preserves_live_item` | 1 | 6, 7, 13 | A selected in-memory item's complete mapping, including list values, stays unchanged while a proposal is shown. | Passed |
| `test_preview_handles_multiple_tracks` | 1 | 8 | Both tracks have separate preview headers and correct proposed titles; neither stored title changes. | Passed |
| `test_preview_handles_no_matches` | 2 | 9 | A query with no matches reports `No matching tracks.` for populated and empty libraries. | 2 passed |
| `test_preview_handles_unchanged_values` | 3 | 3, 10 | Already-correct text and text protected by `all_caps`/`all_lowercase` report `No changes.` without change arrows or persistence. | 3 passed |
| `test_preview_handles_multiple_changed_fields` | 1 | 11 | Album, artist, and title item fields each display their original and proposed values. | Passed |
| `test_preview_handles_list_fields` | 1 | 3, 4, 13 | An `artists` list displays each original and cased element; the stored list stays unchanged. | Passed |
| `test_preview_handles_empty_and_non_string_fields` | 4 | 4, 13 | No configured fields, empty text/lists, numeric/missing fields, and punctuation/numbers-only titles finish with `No changes.` and preserve the stored item. | 4 passed |
| `test_preview_ignores_missing_music_file` | 1 | 7, 13 | Proposals display even when the audio path does not exist and tag writing is enabled. | Passed |
| `test_preview_reports_invalid_query_without_writing` | 1 | 5, 6, 7, 13 | An invalid numeric query raises Beets' existing `InvalidQueryError`; no persistence methods run and the stored title stays unchanged. | Passed |
| `test_normal_command_still_saves_and_respects_tag_write_config` | 2 | 12 | Without preview, title changes persist to the database; actual MP3 tags change only when `import.write` is enabled; the unconfigured artist remains unchanged. | 2 passed |
| `test_preview_then_normal_command` | 1 | 6, 12 | Preview leaves the original stored title, then a normal run stores the proposed title. | Passed |

`PluginTestHelper.run_command()` invokes Beets' real `_raw_main()` argument
parser, plugin loading, query processing, and command callback. The invalid-query
test intentionally expects the backend exception because this helper bypasses
the outer `main()` error-to-exit-message wrapper.

## TDD evidence and actual execution results

The tests were written and run before any plugin implementation change.

| Stage | Actual result | Evidence |
| --- | --- | --- |
| Original titlecase baseline | 12 passed in 0.44 s; 0 failed, 0 errors, 0 skipped | `.reports/a4-baseline.xml` |
| Initial new-test diagnostic run | 35 failed, 2 passed, 1 teardown error in 4.46 s | The teardown error was a test-owned SQLite inspection connection left open on Windows; explicit closure fixed the harness. |
| Recorded red run, original plugin | 35 failed, 2 passed in 4.21 s; 0 errors, 0 skipped | `.reports/a4-red.txt`, `.reports/a4-red.xml`; commit `8319bc0` |
| First green run, preview + existing titlecase | 49 passed in 1.38 s; 0 failed, 0 errors, 0 skipped | `.reports/a4-green.txt`, `.reports/a4-green.xml` |
| Broader regressions, after adding alias coverage | 93 passed in 7.33 s; 0 failed, 0 errors, 0 skipped | `.reports/a4-regression.txt`, `.reports/a4-regression.xml` |
| Final titlecase run after test formatting | 50 passed in 1.42 s; 0 failed, 0 errors, 0 skipped | `.reports/a4-final-titlecase.xml` |

Every failure in the recorded red run occurred because the original subcommand
rejected `-p` with `no such option: -p` (`SystemExit: 2`). The two passing cases
were the normal-command regressions with tag writing disabled/enabled. The
test-first commit contains 37 cases; the later implementation adds one case by
parameterizing the existing CLI test to exercise the `--preview` alias too.
Existing behavioral expectations were retained.

Measured plugin coverage from the 93-case run: **100.00%**, with 149 statements,
58 branches, zero missing statements, and zero partial branches. Coverage XML is
in `.reports/a4-coverage.xml`. This is coverage of the titlecase plugin by the
selected tests, not coverage of the entire repository.

Ruff lint, Ruff formatting, sphinx-lint, and `git diff --check` all passed after
formatting. `.reports/` is ignored by Git: those local artifacts are available
in this workspace and will be regenerated by the commands above. The committed
test file, this results record, and the separate red commit preserve the handoff
for other team members without requiring ignored files.

## Remaining work and useful extensions

There are no unresolved failures or incomplete tests within the requested preview
scope. The entire repository suite was not run. Album mode and combined `-p -a`
are outside Matthew's scope and were not implemented or tested.

Possible extensions for Rami:

- Run the selected suite on Linux/macOS and other supported Python versions.
- Exercise additional audio formats, very long metadata, multiline strings,
  and multiple tracks sharing the same artist/title to inspect readability.
- Add a subprocess smoke test for the installed `beet` entry point and its
  formatted invalid-query exit message using an isolated config and database.
- Expand combinations of existing configuration rules and flexible list fields.
- Coordinate album-mode integration tests with Xuanjia after that feature is
  available, without assuming it is part of this branch.

The unchanged legacy `test_cli_no_write` passes, but its `-p` occurs before
`titlecase`, so it exercises the global plugin option rather than this feature.
The new tests deliberately put preview flags after the subcommand and add actual
database/tag assertions for the normal command with writing disabled.
