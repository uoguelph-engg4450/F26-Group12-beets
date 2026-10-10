# Beets reverse engineering review — ENGG4450 Assignment 1

The existing class diagram covers the complete `beets` source package, including its test helpers, but does not cover the entire repository. Its inheritance is almost complete within that scope. Its associations, inferred field types, and ownership notation need manual refinement before it becomes a useful architectural model.

This review examines the local checkout at commit `83f249b9e64ff842ea9ba4cd0e3764b633af0024`, whose `pyproject.toml` identifies version **2.14.1**. It parses all **303 Python files** and compares declarations and direct bases against both original PlantUML files. The review uses this checkout and its documentation rather than assumptions about another Beets release.

## 1. Repository structure and complete class coverage

| Source area | Python files | Class/schema declarations | In `classes_Beets.puml` | Responsibility |
| --- | ---: | ---: | ---: | --- |
| `beets/`, excluding `beets/test/` | 67 | 203 | 203 | Application core, domain, import, matching, persistence, UI and utilities |
| `beetsplug/` | 96 | 354 | 0 | Optional plugins, metadata providers, API clients and response schemas |
| `beets/test/` | 4 | 29 | 29 | Reusable test helpers, fixtures and mixins |
| `test/` | 133 | 511 | 0 | Test cases, factories, mocks and locally defined test classes |
| `docs/` | 2 | 2 | 0 | Sphinx configuration extension classes |
| `extra/` | 1 | 1 | 0 | Release helper value type |
| **Total** | **303** | **1,100** | **232** | |

The total is **1,098 `class` statements plus two functional `TypedDict` declarations**: `beetsplug.bucket.YearSpan` and `beetsplug.mpdstats.MPDCurrentSong`. These schemas deserve coverage even though they are created through assignment rather than a class statement. The inventory also includes 69 nested/local declarations: one core class, 20 plugin classes, and 48 test classes. Fully qualified lexical names distinguish definitions such as test-local `DummyPlugin` classes.

For an application architecture model, the production scope is **557 declarations: 203 core + 354 plugin**. For the user's literal “entire repository” requirement, the additional **543** test/support/documentation/release declarations need an appendix. Keep that scope distinction explicit in the assignment; test classes should have coverage without dominating the application views.

The complete enumeration is in [CLASS-CATALOG.md](CLASS-CATALOG.md), with a source location, direct bases and home UML view for every declaration. Machine-readable versions are [class-inventory.csv](class-inventory.csv) and [inventory.json](inventory.json). [inheritance.csv](inheritance.csv) lists every explicit base expression and its resolved target: 772 relationships resolved to repository declarations and 318 external or unresolved base expressions. These are direct relationships; transitive inheritance is obtained by following the chains. Implicit `object` inheritance is omitted.

Other repository areas matter to the architectural explanation but do not add Python classes: `docs/` describes the public interfaces and workflows; `.github/` contains automation; `pyproject.toml`, `setup.cfg`, and `uv.lock` describe packaging, dependencies and development checks; `extra/` supports releases.

### Principal inheritance families

| Family | Important direct inheritance |
| --- | --- |
| Music library | `Library → Database`; `LibModel → Model[Library]`; `Album → LibModel`; `Item → LibModel`; `FormattedItemMapping → FormattedMapping` |
| Matching metadata | `Info → AttrDict[Any]`; `AlbumInfo → Info`; `TrackInfo → Info`; `AlbumMatch → Match`; `TrackMatch → Match` |
| Import tasks | `ImportTask → BaseImportTask`; `SingletonImportTask → ImportTask`; `SentinelImportTask → ImportTask`; `ArchiveImportTask → SentinelImportTask` |
| Queries | `FieldQuery → Query`; field/string/numeric/date/path predicates specialize this hierarchy; `CollectionQuery → Query`; `MutableCollectionQuery → CollectionQuery`; `AndQuery` and `OrQuery → MutableCollectionQuery`; `NotQuery → Query` |
| Field types | Numeric, string, path, boolean and date types specialize `Type`; examples include `Integer → BaseInteger`, `Float → BaseFloat`, `String → BaseString`, `DateType → Float`, and `MusicalKey → String` |
| Sorting | `FieldSort → Sort`; `FixedFieldSort`, `SlowFieldSort`, `SmartArtistSort → FieldSort`; `MultipleSort` and `NullSort → Sort` |
| Migrations | Library migrations specialize `Migration`; multi-arranger/composer/genre/lyricist/remixer migrations use `MultiValueFieldMigration` |
| Plugin API | `MetadataSourcePlugin → BeetsPlugin`; `SearchApiMetadataSourcePlugin → MetadataSourcePlugin`, with the additional `Generic[R]` base |
| Metadata plugins | MusicBrainz, Spotify, Deezer and Discogs use `SearchApiMetadataSourcePlugin`; Beatport, Acoustid and Tidal use `MetadataSourcePlugin`; `MusicBrainzPseudoReleasePlugin → MusicBrainzPlugin` |
| Other plugins | Most specialize `BeetsPlugin`; multiple inheritance also matters, for example `LyricsPlugin(LyricsRequestHandler, BeetsPlugin)` and `FetchArtPlugin(BeetsPlugin, RequestMixin)` |
| Artwork strategies | `IMBackend` and `PILBackend → LocalBackend`; fetch-art sources use `ArtSource`, `LocalArtSource` and `RemoteArtSource` |
| Audio/lyrics strategies | ReplayGain implementations specialize `Backend`; `R128Task → RgTask`. Lyrics implementations use a separate `Backend` hierarchy and `SearchBackend(SoupMixin, Backend)` |
| Pipeline execution | First/middle/last worker threads specialize `PipelineThread`, which specializes `threading.Thread`; `CountedQueue → queue.Queue` |
| CLI/logging | `SubcommandsOptionParser → CommonOptionsParser → optparse.OptionParser`; `HelpCommand → Subcommand`; `TerminalImportSession → ImportSession`; `BeetsLogger(ThreadLocalLevelLogger, StrFormatLogger)` |
| HTTP support | API clients specialize `RequestHandler`; `TidalSession(OAuth2Session, TimeoutAndRetrySession)` has multiple inheritance; specialized sessions/adapters build on `requests` |

These examples are an architectural guide; the catalog and CSV provide the exhaustive class and base lists. Distinguish module-qualified classes with repeated names, especially the different `Backend`, `Item`, `Track`, and `ImportAbortError` definitions.

Metaclasses are separate from base classes. For example, `BeetsPlugin` uses `BeetsPluginMeta`; it does **not** inherit from that metaclass. `TimeoutAndRetrySession` uses `SingletonMeta`. Use a note or `<<metaclass>>` dependency for those relationships. `Protocol`, `TypedDict`, `NamedTuple`, enum and dataclass declarations should also be labelled explicitly: event payload schemas are typed dictionaries, not independently instantiated event-dispatch services.

## 2. Review of the existing diagrams

### `classes_Beets.puml`

The file contains **232 class declarations, 118 inheritance arrows, 45 directed associations, nine composition arrows, and 12 aggregation arrows**.

All 232 class identities correspond to source declarations. All 118 inheritance arrows agree with the source. There is one missing direct inheritance relationship between already represented classes:

```plantuml
beets.autotag.hooks.Info --|> beets.util.AttrDict
```

The source declares `class Info(AttrDict[Any])` in [hooks.py](../F26-Group12-beets/beets/autotag/hooks.py). There are therefore 119 direct relationships between the classes in this diagram. External bases such as `logging.Logger`, `threading.Thread`, `optparse.OptionParser`, `ABC`, `Generic`, and `Protocol` are also omitted; show selected external ancestors where they explain the architecture, with an external stereotype.

The **868 omitted repository declarations** are precisely 354 plugin + 511 test + three documentation/release declarations. No core declarations need adding. In particular, regenerating only `beets/` will not recover the plugin classes.

The largest semantic gaps are:

1. **Album–Item membership.** Add `Album "0..1" -- "0..*" Item` with the role `album_id / items()`. An item may be a singleton. `Album.remove(..., with_items=False)` can preserve items, so mandatory composition would overstate lifecycle ownership. These are domain cardinalities, not a claim that SQLite enforces every constraint.
2. **Persistence references.** `Model` keeps a database reference that may be absent before persistence. `Library` registers the `Item` and `Album` model classes, creates albums, and returns `Results`. `Results` materializes models and holds query/sort/database context. These references are more useful than a collection of inferred test-fixture associations.
3. **Matching collections.** `Proposal.candidates` contains album or track matches; `AlbumMatch.mapping` pairs `Item` keys with `TrackInfo` values and also records unmatched objects; `Source.items` holds source items. Several collection relationships appear as field text but lack useful association lines and multiplicities.
4. **Import task state.** Show task items, candidate lists, optional chosen matches, source descriptions, the resulting album, and the session's library reference. The inheritance hierarchy alone does not explain the workflow.
5. **Artwork backend alternatives.** The generated file draws composition to both `IMBackend` and `PILBackend`. [ArtResizer](../F26-Group12-beets/beets/util/artresizer.py) actually selects one available backend or holds `None` when falling back to the web proxy. Prefer `ArtResizer --> "0..1" LocalBackend`, then show its subclasses.
6. **Dictionary associations need roles.** `Distance.tracks` is `dict[TrackInfo, Distance]`. Both generated target associations are meaningful, but label the `TrackInfo` association as keys and the `Distance` self-association as values. They do not indicate two independent lists.
7. **Generated types are inference results.** For example, `AlbumInfo.album_id` is shown as `NoneType`, but its constructor accepts `str | None`; `year` accepts `int | None`. Use the source annotations instead of interpreting a default of `None` as the complete type. Dynamic metadata fields and dictionary-backed library fields require attention beyond ordinary instance attributes.
8. **A query class is not a query instance.** The `query` attributes on database field types select query classes, such as `NumericQuery` or `SubstringQuery`. Label the relationship as a query-class reference or construction dependency, rather than an owned query object.

The generated diamonds are **hypotheses to review**, not proof of ownership. A stored constructor argument does not by itself justify aggregation, and construction inside a method does not establish all UML composition constraints. Plain associations are adequate for shared references such as `Transaction.db`, `ImportSession.lib`, and worker `all_threads`. Composition can be useful when exclusive containment is established, for example a template's internally built expression tree; include that rationale when using it.

Your full generated diagram is useful as an inventory baseline. The amount of attribute/method detail, flattened short class labels and test helper relationships make it difficult to use as the principal architectural illustration. Select operations relevant to each view and put each class under its real module/package.

### `packages_Beets.puml`

The file contains **71 module/package boxes and 329 dependency lines**, using 277 solid `-->` arrows and 52 dotted `..>` arrows. Its boxes cover exactly the Python modules under `beets/`, including test support. It omits the other 232 Python-file modules in the repository. `beetsplug` also has namespace-package behavior; a directory need not have `__init__.py` to belong in the architectural package view.

In this file, dotted arrows correspond to type-checking imports. Make that distinction explicit in a legend. Import dependencies are better shown with dotted UML dependency arrows and labels such as `<<import>>` and `<<typing>>`; a solid class-style association should not be mistaken for a runtime ownership relationship between packages.

The source-import comparison finds **12 direct import pairs between existing boxes absent from the generated diagram**. Examples include `beets.importer.session → beets.importer.stages`, `beets.library.library → beets.library.migrations`, `beets.dbcore.queryparse → beets.dbcore.query/sort`, `beets.dbcore.types → beets.dbcore.query/pathutils`, and `beets.plugins → beets.events`. The full list is in [audit.json](audit.json), and [module-imports.csv](module-imports.csv) records source lines and conditional contexts.

Some other differences involve inference through re-exports, import-time conditions and symbols rather than literal direct module imports. The audit's `diagram_edges_without_direct_import` is a comparison list, **not a list of proven defects**. For example, distinguish the external `mediafile` dependency from the deprecated `beets.mediafile` compatibility wrapper rather than treating the wrapper as Beets' implementation of audio-tag I/O.

Most importantly, this import graph misses dynamic interactions. [plugins.py](../F26-Group12-beets/beets/plugins.py) uses `import_module` to load configured plugins and changes the namespace search path. A plugin's appearance in configuration can create runtime interactions without a corresponding literal import of that plugin in core source.

## 3. Architectural components and interactions

The source supports describing Beets as a **modular application with a plugin framework and an import pipeline**. Calling the plugin framework a microkernel and its backend families strategies is an interpretation of the source design. It is not a distributed microservice system, and its source dependencies do not form perfectly isolated layers.

| Component | Main elements | Interaction |
| --- | --- | --- |
| Startup and CLI | `beets.ui.main`, `_setup`, parsers, `Subcommand`, `beets.ui.commands` | Bootstrap configuration/logging, load plugins, collect built-in/plugin commands, open `Library`, dispatch command functions |
| Import coordination | `ImportSession`, `TerminalImportSession`, task factory, task subclasses, actions and `ImportState` | Build tasks, look up/choose candidates, resolve duplicates, persist music, run plugin stages, handle files and finalize progress |
| Import execution | `beets.importer.stages` functions and `Pipeline`/worker threads | Pass tasks through generator/coroutine stages; run sequentially or using bounded queues and worker threads |
| Autotag/matching | `Source`, `Info`, `AlbumInfo`, `TrackInfo`, matches, `Distance`, `Proposal`, `Recommendation` | Match source items to provider metadata, compute distances, rank proposals and apply selected metadata |
| Metadata providers | `MetadataSourcePlugin`, `SearchApiMetadataSourcePlugin`, provider plugins and API clients | Search/get metadata through hooks; shared orchestration uses `ThreadPoolExecutor` for provider I/O |
| Domain/persistence | `Library`, `Item`, `Album`, `LibModel`, `Database`, `Model`, `Transaction`, `Results`, queries/sorts/types/migrations | Persist and query library metadata in SQLite; handle fixed and flexible fields and schema evolution |
| Plugin extensions/events | `BeetsPlugin`, metaclass, module-level registry/listeners, `beetsplug.*`, event schemas | Add commands, queries, fields, templates, import stages and synchronous event callbacks |
| File and presentation support | External `mediafile`, path/template helpers, art resize backends, config/logging | Read/write tags, compute destinations, move/copy/link files, manage artwork and format output |

The application entry point is `beet = beets.ui:main` in [pyproject.toml](../F26-Group12-beets/pyproject.toml). [UI setup](../F26-Group12-beets/beets/ui/__init__.py) loads plugins and appends their commands before opening the library.

An ordinary album import follows this path:

1. `ImportSession.run()` constructs producer and processing coroutines and starts a `Pipeline`.
2. A task factory reads source items; lookup calls `tag_album` or `tag_item`, which uses configured metadata providers.
3. The CLI session selects a match/action; duplicate handling and metadata application occur in the choice stage. Import-as-is bypasses metadata lookup.
4. Tasks add/store the album and items through the library. Configured fields are then applied.
5. Early/regular plugin stages run after choice/application and database insertion, before final file handling.
6. File handling performs configured operations and tag writing, then finalization updates progress, cleanup and import events.

This ordering follows [session.py](../F26-Group12-beets/beets/importer/session.py), [stages.py](../F26-Group12-beets/beets/importer/stages.py), and [tasks.py](../F26-Group12-beets/beets/importer/tasks.py). Pretend, singleton, skip, merge, upgrade, rescan and reimport modes introduce branches; the sequence diagram deliberately illustrates the ordinary album path.

The event dispatcher is **`beets.plugins.send`**, with listeners registered through `BeetsPlugin`; [beets.events](../F26-Group12-beets/beets/events.py) describes event names and typed payloads. Do not invent a `PluginManager`, `EventBus`, `ImportStage`, or `MusicBrainzClient` class where the repository instead has module functions or differently named API classes.

Useful cross-component associations include `ImportSession → Library`, `ImportTaskFactory → ImportSession`, `BaseImportTask → Item[*]`, `ImportTask → Match[0..1]`, `AlbumMatch → AlbumInfo/Item/TrackInfo`, `Match → Distance`, `AlbumInfo → TrackInfo[*]`, and `Proposal → Match[*]/Recommendation`. `Item → MediaFile` is a creation/use dependency: each file read/write constructs a temporary media-file object rather than owning a permanent one.

Plugin detail views should preserve their collaborators as well as the base class: `FetchArtPlugin → ArtSource[*]/Candidate`; `ArtResizer → LocalBackend[0..1]`; `LyricsPlugin → Backend[*]`; `ReplayGainPlugin → Backend/RgTask/Gain`; and API clients → reusable HTTP sessions/adapters. The optional web/AURA/BPD interfaces are plugins, so they belong in extension views rather than replacing the CLI as the application core.

Selected, source-reviewed UML models accompany the report: [architecture.puml](architecture.puml), [domain-relationships.puml](domain-relationships.puml), [matching-relationships.puml](matching-relationships.puml), [plugin-relationships.puml](plugin-relationships.puml), and [import-workflow.puml](import-workflow.puml).

## 4. Recommended UML split and coverage method

Use two levels: a small set of explanatory architectural/relationship/workflow figures in the assignment narrative, and a traceable class appendix for full coverage. The five curated views above are suitable starting points for the narrative. The appendix uses these **16 core home views**, covering all 203 core declarations without counting references twice:

| Core view | Owned declarations | Scope |
| --- | ---: | --- |
| Library/domain | 9 | Models, library and file exceptions |
| Database support | 12 | Database, model, transaction, results, mappings, index/schema support |
| Query predicates | 19 | Field predicates, date values and parsing exceptions |
| Query combinations | 8 | Base query and logical collection/combinator hierarchy |
| Field types | 23 | Storage/conversion/formatting type hierarchy and constructor protocol |
| Sorting | 7 | Sort hierarchy |
| Migrations | 11 | Library migration hierarchy and value record |
| Importer | 18 | Sessions, tasks, archive adapters/protocols, factory, actions and state |
| Autotag | 10 | Metadata, source, matching, distance and proposal values |
| Plugin contracts | 8 | Plugin/source base classes, metaclass, errors and search values |
| CLI | 19 | Parsers, command/option types and import display/session classes |
| Events | 18 | Typed payload schemas |
| Shared support | 21 | Config, logging, descriptors, general utilities, lyrics/playlist/layout values |
| Art resizing | 6 | Resizer, backend types, availability/error types |
| Templates | 7 | Parser, expression/call/symbol/environment/template and error |
| Pipeline | 7 | Pipeline, workers, queue and multimessage |
| **Total** | **203** | |

For extensions, retain module boundaries, especially the substantial fetch-art, lyrics, ReplayGain, BPD, Spotify and HTTP-client hierarchies. Put API payload definitions (`_typing`, MusicBrainz/Discogs/Tidal response types) in schema views. The supplied coverage draft uses **94 plugin views**, paginating modules with more than 20 declarations; it shows all 354 plugin declarations. For presentation, related small command plugins can be grouped by responsibility, provided their individual classes remain traceable.

Put reusable `beets/test` helpers in their own appendix (**four views**) and test classes in an appendix organized by test module (**118 views**, with large modules paginated at 20 declarations). The two Sphinx extension classes and release `Ref` share one supporting view. These many small appendix views are an exhaustive reference, not a recommendation to present 233 figures during a talk.

The [MODEL-INDEX.md](MODEL-INDEX.md) links all **233 names-only coverage views**. [model-membership.csv](model-membership.csv) assigns every one of the 1,100 declarations to exactly one home view. Cross-view superclass references carry `<<reference>>`; external or unresolved bases carry `<<external>>`. Parameterized base expressions are retained as comments and in the inventory.

To keep explanatory models readable:

- Target roughly 10–25 relevant classes per page, allowing more space for association-heavy views. Split large hierarchies at a meaningful base class.
- Show a superclass/collaborator again as a labelled reference when necessary; count only its home declaration in the coverage table.
- Use module packages and fully qualified identity in the index to disambiguate repeated short names.
- Include selected operations such as `run`, `lookup_candidates`, `apply_metadata`, `add_album`, `read`, `write`, and `transaction`. Suppress routine methods and large field lists in overview views.
- Use multiplicities and role names on important collections; distinguish instance associations, class references, creation/use dependencies and metaclasses.
- Show function-based modules in component/package or workflow diagrams. Classes alone cannot represent every important Python responsibility.
- Keep the unabridged source inventory and dependency CSVs as evidence even when the narrative suppresses minor edges.

## Verification and practical limits

All 303 Python files parsed successfully. The coverage checks found **zero unassigned declarations, zero duplicate home assignments, and zero undeclared inheritance endpoints** in the generated appendix. Original PlantUML input hashes are recorded in [audit.json](audit.json), and the original diagrams and application source were left unchanged. The analysis outputs live in the sibling `assignment1-analysis/` directory.

This is static reverse engineering. Import resolution follows source imports/re-exports conservatively; function-local aliases, arbitrary metaprogramming, dynamically configured third-party plugins, and external dependency classes cannot be fully established without runtime inspection. Classes supplied by dependencies such as `mediafile`, Flask or `requests` are external references rather than new repository declarations. `typed-references.csv` contains annotation-based relationship candidates and signature dependencies; it is not an assertion that all such candidates are owned instance fields.

The generated appendix is **names and direct inheritance only**. Its declaration coverage is complete for the scanned source, but it does not claim exhaustive runtime association coverage or finished visual layout. The curated models add the main associations and behavior. A PlantUML renderer was unavailable, so structural checks were performed; the files were not rendered or visually inspected. See [coverage-validation.json](coverage-validation.json).

To reproduce the analysis from this directory:

```text
python analyze_repository.py
python build_split_models.py
```

No application code imports, dependency installs, repository commits, or external service operations are needed for those scripts.
