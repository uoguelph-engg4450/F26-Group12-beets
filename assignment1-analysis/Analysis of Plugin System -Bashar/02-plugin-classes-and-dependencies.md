# Task 2 – Main plugin classes, extension mechanisms, dependencies

(See `01-plugin-support.md` for the scope note; **[verify]** marks items to confirm in source.)

## Main classes and modules

| Element | Location | Role |
|---------|----------|------|
| `BeetsPluginMeta` | `beets.plugins` | Metaclass on `BeetsPlugin`; wraps/auto-registers plugin behaviour (e.g. listener and logging setup) at class creation. |
| `BeetsPlugin` | `beets.plugins` | Base class for every plugin. Holds `name`, `config`, `_log`, listeners, `commands()`, stage lists, template funcs/fields, type declarations. |
| `MetadataSourcePlugin` | `beets.metadata_plugins` | Abstract specialization: a plugin that can supply `AlbumInfo` / `TrackInfo` by id or search. |
| `SearchApiMetadataSourcePlugin<R>` | `beets.metadata_plugins` | Abstract helper for providers with a search REST API; builds queries (`get_search_query_with_filters`) and fetches results (`get_search_response`) using `SearchParams`. |
| `SearchParams` | `beets.metadata_plugins` | Namedtuple handed to the provider hook. |
| Registry functions | `beets.plugins` (`load_plugins`, `find_plugins`, `send`, `commands`, `queries`, `types`, ...) | Module-level functions, **not** a `PluginManager` class. |
| `beets.events` | `beets.events` | Declares event names and payload schemas. |
| `Subcommand` | `beets.ui` | Returned from `commands()`. |
| Concrete examples | `beetsplug.*` | `MusicBrainzPlugin`, `SpotifyPlugin`, `AcoustidPlugin` (chroma), `TidalPlugin`, plus ~70 others (fetchart, lyrics, convert, web, ...). |

## Extension mechanisms, mapped to core consumers

| Mechanism | Declared by plugin | Consumed by core |
|-----------|-------------------|------------------|
| Subcommands | `commands()` | `beets.ui` (`_setup`/`_raw_main`) |
| Event listeners | `register_listener` | any core code calling `plugins.send(...)` (library, importer, ui) |
| Import stages | `early_import_stages`, `import_stages` | `beets.importer` pipeline construction |
| Metadata provider hooks | `MetadataSourcePlugin` methods | `beets.metadata_plugins` → `beets.autotag` |
| Distance hooks | `track_distance`, `album_distance` | `beets.autotag.match` |
| Templates | `template_funcs`, `template_fields` | `beets.library` / `beets.util.functemplate` |
| Types/queries | `item_types`, `album_types`, `queries` | `beets.dbcore` / `beets.library` |
| Media fields | `add_media_field` | `mediafile` |

## Dependencies (direction matters)

* Core → plugins: **only** via `beets.plugins` / `beets.metadata_plugins` (registry, dynamic import).
* Plugins → core: freely import `beets.library`, `beets.ui`, `beets.autotag`, `beets.util`, `beets.dbcore`. This is a wide, public-by-convention API.
* Plugins → third-party libs: per-plugin, mostly optional extras.
* Plugins → plugins: discouraged; occasional direct imports or shared helpers (e.g. `beetsplug._utils`) **[verify]**.

## Observations about the class model
* The hierarchy is shallow (Plugin → MetadataSource → SearchApi → concrete), which keeps most plugins at one level of inheritance.
* Most plugin capability is "optional override" on a fat base class rather than separate interfaces.
