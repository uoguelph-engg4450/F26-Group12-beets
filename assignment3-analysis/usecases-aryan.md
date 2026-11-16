UC-01: Titlecase tracks matching a query

Primary actor: Beets user
Goal / trigger: The user wants consistent capitalization in their track metadata. They run beet titlecase with an optional query.
Preconditions: The titlecase plugin is enabled. The fields setting lists at least one field to change. The library contains tracks. The user can modify the library database (and the music files, if tag writing is on).
Main success flow:
The user runs the titlecase command, optionally with a query such as an artist name.
The system finds the matching tracks (UC-05).
For each track, the system applies the configured titlecase rules to the configured fields.
The system saves the updated metadata to the library.
If Beets is set to write tags, the system also updates the music files.
The system reports each track it processed.
Alternative paths:
A1. No query given at step 1: all tracks in the library are processed.
A2. A field is already correctly capitalized: it is left unchanged.
A3. Tag writing is switched off: step 5 is skipped, so only the library is updated.
A4. The user adds -p: see UC-02. The user adds -a: see UC-03.
Exceptions:
E1. No tracks match the query: nothing is processed or changed.
E2. No fields are configured: no metadata changes, so the user must add fields to the configuration.
E3. A music file cannot be written (for example, it is read-only or missing): that file’s tags are not updated, the system reports a problem, and the remaining tracks are still processed.
E4. The query is invalid: the system shows an error and processes nothing.
Postconditions: Success: the configured fields of all matching tracks are titlecased in the library (and in file tags if writing is on); album records are unchanged. Failure: tracks that were not processed keep their previous values.
Related requirements: [FR/QR IDs once frozen]

UC-02: Preview proposed titlecase changes (-p)

Primary actor: Beets user
Goal / trigger: The user wants to see what titlecase would change before anything is modified. They run beet titlecase -p with an optional query.
Preconditions: Same as UC-01, and the -p option is available.
Main success flow:
The user runs the titlecase command with -p and an optional query.
The system finds the matching tracks (UC-05).
For each track, the system works out the titlecased values without saving them.
The system shows each track that would change, with each field’s current and proposed value.
The system makes clear that nothing was changed.
The user reviews the output, then either runs UC-01 to apply the changes or adjusts the configuration and previews again.
Alternative paths:
A1. Nothing would change: the system tells the user the tracks are already correct.
A2. No query given: the whole library is previewed.
A3. The user adds -a: see UC-04.
A4. The user changes the titlecase settings and reruns -p to compare.
Exceptions:
E1. No tracks match the query: nothing is shown.
E2. No fields are configured: no changes are shown.
E3. The query is invalid: the system shows an error.
Postconditions: Success: the user has seen the proposed changes, and the library and music files are identical to before. Failure: nothing changed.
Related requirements: [FR/QR IDs once frozen]

UC-05: Select tracks or albums by query

Primary actor: Beets user
Goal / trigger: The user wants to clean up only part of their library, so they add query terms after the command.
Preconditions: The library exists and the user knows the query syntax (for example a field match or a folder path).
Main success flow:
The user types query terms after the command.
The system searches the library for matches (tracks by default, albums when -a is used).
The system passes the matches to the use case that is running.
Alternative paths:
A1. No query: everything matches.
A2. Several terms: an item must match all of them.
A3. The user gives a folder path, as in the original issue.
Exceptions:
E1. Nothing matches: the calling use case ends with no changes.
E2. The query is invalid: the system shows an error and selects nothing.
Postconditions: Success: the matching items are identified and left unchanged. Failure: nothing is selected.
Related requirements: [FR/QR IDs once frozen]