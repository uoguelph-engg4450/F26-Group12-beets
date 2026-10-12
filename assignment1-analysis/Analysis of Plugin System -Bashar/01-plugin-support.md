# Task 1 – How beets supports plugins and extensions

> Scope note: this analysis was written from the supplied PlantUML diagrams and
> knowledge of the beets codebase (`beets/plugins.py`, `beets/metadata_plugins.py`,
> `beets/events`, `beetsplug/*`). It was not checked line-by-line against a fresh
> checkout; items marked **[verify]** should be confirmed against the repo.

## 1. Plugins are first-class, in-process Python packages

Beets has no out-of-process plugin protocol. A plugin is a Python module that
is imported into the running `beet` process and instantiated once. Everything
else (CLI, importer, library) talks to plugins through a small registry in
`beets.plugins`.

## 2. Discovery and loading

| Step | Mechanism |
|------|-----------|
| Opt-in | The user lists plugin names under `plugins:` in `config.yaml`. Nothing loads by default. |
| Namespace | Built-in plugins live in the `beetsplug` namespace package. Third-party plugins also install into `beetsplug`, so `beetsplug.<name>` resolves regardless of which distribution ships it. |
| Extra paths | `pluginpath:` in config appends directories to `beetsplug.__path__` for local, uninstalled plugins. |
| Import | `beets.plugins.load_plugins()` imports `beetsplug.<name>` and scans the module for `BeetsPlugin` subclasses. |
| Instantiate | Each subclass is instantiated once; instances are cached (`_instances`) and returned by `find_plugins()`. |
| Failure handling | Import errors are logged and the plugin is skipped; the rest of beets keeps running. **[verify]** exact behaviour differs between versions. |

Entry point in the diagrams: `cli ..> plugins : load plugins / collect commands`
(architecture.puml) and `plugins ..> extensions : dynamic import and instantiate`.

## 3. Extension mechanisms (what a plugin can contribute)

A plugin extends beets by overriding attributes/methods on `BeetsPlugin` or by
calling registration helpers in `__init__`.

1. **CLI subcommands** – `commands()` returns `beets.ui.Subcommand` objects that are merged into the `beet` CLI.
2. **Event listeners** – `register_listener(event, func)` (or the `@listen`-style helpers) subscribes to named events (e.g. `album_imported`, `item_moved`, `write`, `library_opened`). `plugins.send(event, **kwargs)` dispatches to all listeners. Event names and payload schemas are declared in `beets.events`.
3. **Import pipeline stages** – `early_import_stages` and `import_stages` inject extra coroutine stages into the importer pipeline.
4. **Template functions and fields** – `template_funcs`, `template_fields`, `album_template_fields` extend path formats and `$field` / `%func{}` expressions.
5. **Query types and field types** – `item_types` / `album_types` declare typed flexible attributes; `queries` / named queries add custom query prefixes.
6. **Media fields** – `add_media_field()` registers extra tags with `mediafile` so they can be read/written.
7. **Distance and candidate hooks** – `track_distance`, `album_distance`, `candidates`, `item_candidates` let a plugin influence autotag matching and propose candidates.
8. **Metadata providers** – subclasses of `MetadataSourcePlugin` (in `beets.metadata_plugins`) implement `album_for_id`, `track_for_id`, search hooks, etc., so the autotagger can query them uniformly. `SearchApiMetadataSourcePlugin` adds a template for REST-style search providers.
9. **Per-plugin configuration** – each plugin gets its own `config[<plugin name>]` subview (confuse) with defaults registered by the plugin.

## 4. Important dependencies

* **confuse** – layered YAML configuration used for core and every plugin.
* **mediafile** (+ mutagen) – tag read/write; plugins may add fields.
* **beets.dbcore / beets.library** – plugins query and mutate `Item`/`Album`; they can add field types to the schema.
* **beets.ui** – `Subcommand`, option parsing, prompts, `UserError`.
* **beets.util.pipeline** – import stage execution.
* **Third-party libs per plugin** – e.g. `requests`, `musicbrainzngs`, `flask` (web), `pyacoustid` (chroma), `mutagen`, `jellyfish`. These are optional extras so core installs stay light.

## 5. Summary

Beets uses a **registry + hook** model: a tiny central module owns loading and
event dispatch; the core calls out to plugins at well-defined seams (CLI
assembly, import stages, metadata search, template evaluation, model events).
Plugins do not call each other directly; they interact through core services.
