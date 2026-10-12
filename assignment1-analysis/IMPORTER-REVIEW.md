# The import subsystem

Importing is Beets' central use case. The user points Beets at a folder of music files. Beets identifies each album against online metadata sources, corrects the tags, records the music in its library database and organizes the files into the library directory. This section explains how the import subsystem is designed and how it works with metadata matching, the database and plugins. It then assesses the design's strengths and weaknesses. The analysis is based on the source code of Beets 2.14.1.

## Overview

*Figure 1 ([importer-class.puml](importer-class.puml)): The main classes of the import subsystem, grouped by package.*

Figure 1 shows the main classes of the import subsystem. `ImportSession` coordinates one import run. It holds a reference to the `Library` and creates the `Pipeline` that processes the music. The work itself is represented by `ImportTask` objects, one per album, which an `ImportTaskFactory` creates from the files it finds on disk. Each task holds the album's `Item`s, the candidate matches found for it and, once the album is stored, the resulting `Album`. `SingletonImportTask` handles a single track. `SentinelImportTask` carries no music; it only marks the end of a folder.

Two parts of the import are delegated outside the `beets.importer` package. Decisions are made by a subclass of the session: `TerminalImportSession`, in the user-interface package, prompts the user. Metadata comes from `MetadataSourcePlugin` subclasses, which produce `AlbumInfo` objects. The autotagger wraps these as `AlbumMatch` candidates inside a `Proposal`.

## Import workflow

*Figure 2 ([import-activity.puml](import-activity.puml)): The import pipeline for one album.*

An import is organized as a **pipeline**, shown in Figure 2. Each task passes through a fixed series of stages:

1. reading files into items;
2. looking up metadata candidates;
3. choosing a match;
4. applying the metadata and adding the album to the database;
5. running plugin stages;
6. moving or copying the files and writing their tags.

When autotagging is turned off, a single "import as-is" stage replaces lookup and choice. Choices such as "import as separate tracks" or "rescan the folder" do not continue down the pipeline. Instead, they create new tasks that re-enter lookup and choice.

By default each stage runs in its own thread, and the stages are connected by bounded queues. Several albums are therefore in progress at once. While the user is deciding about one album, the metadata lookup for the next album is already running.

*Figure 3 ([import-sequence.puml](import-sequence.puml)): The interaction between a task, the autotagger, the metadata providers and the session during lookup and choice.*

Figure 3 shows the step that involves the most collaborators. The task asks the autotagger to tag the album. The autotagger queries the providers, scores and ranks their results, and returns a `Proposal`. The task then asks the session to choose. A strong match can be accepted automatically; otherwise the user is shown the candidates.

## Interactions with matching, the database and plugins

**Metadata matching.** The importer depends on the autotagger through just two functions, `tag_album` and `tag_item`, which both return a `Proposal`. The autotagger contains no metadata source of its own. It calls every loaded `MetadataSourcePlugin` concurrently in a thread pool, merges their results and ranks each candidate by its distance from the files' current tags. Even MusicBrainz, the default source, is a plugin. Applying a match copies the selected metadata onto the in-memory `Item`s.

**The database.** The album is written to the database *before* any file is touched. Inside one transaction, `ImportTask.add()` removes any items being replaced and creates the `Album` row with its `Item` rows. The duplicate check queries the library just before this step. After the files have been moved, their new paths are stored. Later stages, including plugin stages, therefore work with fully persisted records.

**Plugins.** Plugins take part in three ways:

- Metadata providers supply match candidates.
- Plugins can register extra pipeline stages, which run after the database write and before file handling.
- Plugins can listen to events that the importer sends at each step, such as `import_task_created`, `import_task_choice` and `album_imported`.

Events are delivered synchronously, and some listeners' return values change the import: a plugin can replace a task with other tasks, or change the user's choice.

## Strengths

- **A pipeline of small stages.** Each stage is a short generator function with one job, and the same stage list can run sequentially or in parallel. Running the stages in parallel overlaps slow network lookups with the user's decisions, without making the stage code itself concurrent.
- **Extensible without changing the core.** The session assembles the stage list at run time from the configuration and the loaded plugins. Plugins can add stages, react to events and supply metadata without any change to the importer.
- **The user interface is separated from the logic.** `ImportSession` leaves its decisions to subclasses (Figure 1). The terminal interface is one implementation, and the test suite supplies another that answers automatically.
- **Metadata sources are interchangeable.** Because all providers are plugins with a common interface, adding a new source requires no change to the matching code.

## Weaknesses and possible improvements

1. **The task class hierarchy is inverted.** In Figure 1, both `SingletonImportTask` and `SentinelImportTask` inherit from the album task. The singleton task has to override album behaviour with incompatible types, and the sentinel overrides most methods to do nothing. The source itself notes that "the inheritance relationships are inverted". Because a sentinel or skipped task can arrive at any stage, every stage also begins with the same "skip this task" check. *Improvement:* put the shared behaviour in the base task, make album and singleton tasks siblings, model sentinels as a separate control message, and filter skipped tasks once in the pipeline.
2. **The user's choice is loosely typed.** A single `Action` value mixes metadata decisions (apply, as-is, skip) with choices that restructure the pipeline (as tracks, group albums, rescan). The chosen match is stored in a second field, and the two must be kept consistent by hand. *Improvement:* return a small result object that holds the choice and an optional match, and handle the restructuring choices separately.
3. **Plugin stages can write directly to the database.** As a result, the importer reloads the task's items from the database after every plugin stage. *Improvement:* have plugins change the task's in-memory objects, and save them once at the end.
4. **The importer depends on global state.** Stages and tasks read the global configuration directly, and the session modifies it to resolve conflicting options. Event listeners are also stored globally. This makes the importer hard to test in isolation or to run twice in one process. *Improvement:* pass an immutable options object to the session and its stages.
5. **The database is written before the files are handled.** If the import fails between these two steps, the library contains records that point to files that were never moved. *Improvement:* mark records as pending until the file stage succeeds, or keep a journal of planned file operations and complete or roll it back on the next run.
