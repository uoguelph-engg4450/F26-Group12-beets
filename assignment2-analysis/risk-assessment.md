| Risk | Potential problem | Mitigation | What happened |
|---|---|---|---|
| Missing dependencies | Tests cannot execute | Use a virtual environment; install the test extras and BeautifulSoup (`python -m pip install -e ".[test]"`, `python -m pip install beautifulsoup4`); `uv sync` for #6770 | Occurred for #7070: running the full lyrics suite raised module errors (confuse, unidecode, bs4) |
| Platform differences | Windows-specific test failures | Run the lyrics tests with `--basetemp=C:\tmp\beets-pytest` | Occurred for #7070: a temporary-directory permission error during testing |
| Regression errors | A fix breaks existing behaviour | Run the complete plugin test suites after each fix | Did not occur: lyrics suite 155 passed, 16 skipped, 0 failed; Tidal suite 62 passed, 0 failed |
| Merge conflicts | Changes from different branches conflict | One branch per issue (Matthew-Changes for #7070, Xuanjia-issue-6770 for #6770), reviewed before merging | Both fixes are now merged into main |
| Unclear final merge target | The TA cannot tell which version is the new release | Agree on one branch for the final version | Resolved: both fixes are in main |
| Limited test realism | Mocked tests miss live-service behaviour | State the limitation in each Testing Evaluation | Both fixes were tested with predefined inputs or mocked API responses, not live LRCLIB or Tidal calls |
| Inconsistent test tooling | Different commands per issue cause confusion | Write out the exact command for each issue in the acceptance tests | #7070 uses `python -m pytest`; #6770 uses `uv run pytest` |
| Time constraints | Issues take longer than planned | Choose small, targeted fixes over ambitious ones | #5998 (needs broader investigation) was not selected; the two chosen fixes were small and testable |

### Problems encountered and adjustments

Two problems occurred while implementing the fixes. For Issue #7070, running the complete lyrics test suite failed at first because optional dependencies were missing (confuse, unidecode and bs4). We resolved this by installing the project's test extras and BeautifulSoup in the virtual environment, and we recorded the commands in the acceptance tests so a TA can reproduce the setup. A Windows temporary-directory permission error also appeared during testing, which we avoided by pointing pytest at a directory we control with the `--basetemp` option.

The two issues were developed independently on separate branches, so the main coordination risk was the final merge. Both fixes were merged into the main branch, so the final repository contains both. We also limited scope by preferring two small, testable fixes over broader issues, and we documented that our tests used mocked data rather than live services, so the results verify the plugin logic but not the external APIs.