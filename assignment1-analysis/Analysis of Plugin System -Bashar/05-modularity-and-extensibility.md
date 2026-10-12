# Task 5 – Modularity and extensibility of the plugin system

## Why it is modular
1. **Opt-in loading.** Only plugins named in `plugins:` are imported; unused features cost nothing at runtime and their dependencies need not be installed.
2. **Single seam.** Core depends on `beets.plugins` (registry/events) and abstract contracts, never on a concrete plugin. Adding a plugin requires zero core changes.
3. **Namespace package.** `beetsplug` lets built-in and third-party plugins coexist and be installed independently (pip), or loaded from a local `pluginpath`.
4. **Fault isolation (partial).** A plugin failing to import is skipped; exceptions in listeners are generally contained by the caller, though a misbehaving plugin can still hurt in-process.
5. **Namespaced config.** `config[<plugin>]` keeps settings isolated and layered with user overrides.

## Why it is extensible
| Need | Extension point |
|------|-----------------|
| New command | `commands()` |
| React to lifecycle | `register_listener` + `beets.events` |
| New import behaviour | import stages |
| New metadata source | `MetadataSourcePlugin` / `SearchApiMetadataSourcePlugin` |
| Influence match scoring | distance / candidate hooks |
| New fields, types, queries, path functions | `item_types`, `queries`, `template_*` |
| New tags in files | `add_media_field` |

A plugin can combine several of these (e.g. `convert` adds a command, a listener, and config; `lyrics` adds a command, a stage listener and a template field).

## Patterns at work
* **Registry** (loaded instances), **Observer / event bus** (`send`/listeners), **Template Method** (`MetadataSourcePlugin`/`SearchApi...` skeletons with hooks), **Chain/pipeline** (importer stages), **Plugin via namespace packages**.

## Cost of the flexibility
Plugins run in-process with full access to core internals, so extensibility is bought with a large implicit API surface (see Task 6).
