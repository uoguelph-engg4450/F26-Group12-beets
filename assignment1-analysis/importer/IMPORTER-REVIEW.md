# The import subsystem

Importing is Beets' central use case: it identifies each album in a folder of music files, corrects the tags, records the music in the database and moves the files into the library. The import subsystem coordinates these steps across every other subsystem.

## Classes and relationships

*Figure 1 ([importer-class.puml](importer-class.puml)): The main classes of the import subsystem, grouped by package.*

`ImportSession` coordinates one import run. An `ImportTaskFactory` turns the input folders into `ImportTask` objects, one per album, and these tasks pass through a `Pipeline` that the session creates.

The model has three kinds of relationship:

- **Inheritance.** The importer has two hierarchies. `TerminalImportSession` specializes `ImportSession` to make decisions through user prompts. `SingletonImportTask` (one track) and `SentinelImportTask` (an end-of-folder marker that carries no music) specialize `ImportTask`.
- **Associations.** The session refers to exactly one `Library`. Each task holds many `Item`s, zero or more candidate `AlbumMatch`es and at most one stored `Album`. The only composition is `AlbumInfo` and its `TrackInfo`s, which exist only as part of it.
- **Dependencies.** «create» dependencies show that the session builds the pipeline, the factory builds the tasks, and provider plugins build the `AlbumInfo` objects.

## Import workflow

*Figure 2 ([import-activity.puml](import-activity.puml)): The import pipeline for one album.*

Each task passes through a fixed series of pipeline stages (Figure 2):

1. read the files;
2. look up metadata candidates;
3. choose a match;
4. apply the metadata and add the album to the database;
5. run plugin stages;
6. move the files and write their tags.

When autotagging is off, a single "import as-is" stage replaces lookup and choice. By default each stage runs in its own thread, and the stages are connected by bounded queues. As a result, one album's lookup runs while the user is still deciding about the previous one. Figure 3 ([import-sequence.puml](import-sequence.puml)) shows the lookup-and-choice interaction in detail.

The importer meets three other subsystems:

- **Metadata matching.** The importer calls only `tag_album` or `tag_item` and receives a ranked `Proposal`. How candidates are found and scored is covered in the Metadata Matching section.
- **Database.** The album and its items are added in one transaction *before* any file is moved. Their new paths are stored after the move. Storage itself is covered in the Library and Database section.
- **Plugins.** Plugins add pipeline stages, which run between the database write and file handling, and they receive an event at each step. The plugin mechanism is covered in the Plugin Architecture section.

## Strengths

- **The stages are small and run either sequentially or in parallel.** Network lookups overlap with user decisions, and the stage code itself does not have to handle threads.
- **The importer is extensible.** The stage list is assembled at run time from the configuration and the loaded plugins, so plugins extend the import without any change to the core.
- **The user interface is separated from the logic.** The session leaves its decisions to subclasses. The terminal and the test suite each supply their own.

## Weaknesses and possible improvements

1. **The task hierarchy is inverted** (Figure 1). The single-track and sentinel tasks inherit album behaviour that they must override or disable, and the source code itself notes this. *Improvement:* make album and single-track tasks siblings, and model sentinels as a separate control message.
2. **The user's choice is loosely typed.** One `Action` value mixes metadata decisions with choices that restructure the pipeline, and the chosen match is kept in a separate field. *Improvement:* return one result object that holds both.
3. **Plugin stages can write to the database directly**, which forces a reload after every plugin stage. *Improvement:* have plugins change the task's objects in memory, and save them once.
4. **The importer depends on global configuration and global event listeners**, which makes it hard to test in isolation. *Improvement:* pass an immutable options object to the session and its stages.
5. **The database is written before the files are moved.** A failure between the two steps leaves records that point to the old file paths. *Improvement:* mark the records as pending until the file stage succeeds.

## Source files

- `beets/importer/session.py`: `ImportSession` and pipeline construction
- `beets/importer/stages.py`: the pipeline stage functions
- `beets/importer/tasks.py`: `ImportTask` and its subclasses, and `ImportTaskFactory`
- `beets/util/pipeline.py`: `Pipeline` and its sequential and threaded execution
- `beets/ui/commands/import_/session.py`: `TerminalImportSession`
- `beets/autotag/match.py`: `tag_album`, `Proposal` and `AlbumMatch`
- `beets/metadata_plugins.py`: `MetadataSourcePlugin` and the provider lookups
- `beets/plugins.py`: plugin import stages and event dispatch
- `beets/library/library.py`: `Library.add_album`
