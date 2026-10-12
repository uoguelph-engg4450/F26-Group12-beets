# Task 6 – Strengths, weaknesses, potential improvements

## Strengths
* **Very low barrier to entry**: a plugin can be a single file subclassing `BeetsPlugin`.
* **Core stays small and stable**; the ecosystem (70+ built-in plugins plus third-party) scales without core changes.
* **Rich, composable seams**: commands, events, stages, templates, types, providers.
* **Uniform provider abstraction** lets the autotagger treat MusicBrainz, Discogs, Spotify, etc. identically.
* **Simple mental model**: one registry, one event bus, one config tree.
* **Optional dependencies** keep base install light.

## Weaknesses
| Area | Issue |
|------|-------|
| Fat base class | `BeetsPlugin` accumulates many optional hooks; capabilities are discovered by reading code rather than declared interfaces. |
| Implicit API | No explicit public/stable plugin API boundary; plugins import many core modules, so internal refactors break third parties. |
| Loose typing of events | Events are string names with kwargs payloads; historically dispatched dynamically (`beets.events` improves this by declaring schemas). |
| Hidden ordering | Listener and stage order depends on load order; plugin interaction/conflicts (e.g. two plugins editing the same field) are not mediated. |
| Global state | Module-level registry/instance cache complicates testing, reloading and multi-library embedding. |
| Isolation | In-process, same interpreter: no sandboxing, a slow or crashing plugin degrades the whole run; dependency version conflicts between plugins are possible. |
| Dependency declaration | Plugins do not declare dependencies on other plugins or core version ranges in a machine-readable way; failure surfaces at runtime. |
| Namespace sharing | Third-party packages writing into `beetsplug` can collide on names. |
| Metadata hierarchy churn | Provider base classes have moved/changed, so documentation and diagrams age quickly. |

## Potential improvements
1. **Define a stable, documented plugin API** (e.g. `beets.plugin_api` re-exports) with a deprecation policy and a plugin API version check.
2. **Capability mixins / Protocols** (`HasCommands`, `ImportStagePlugin`, `MetadataProvider`) in place of one large optional-override base; enables static checking and clearer docs.
3. **Typed events everywhere**: finish moving to `beets.events` typed payloads and have listener registration validated (typos fail fast).
4. **Explicit ordering/priority** for listeners and stages, plus conflict detection for plugins writing the same field.
5. **Use packaging entry points** (`beets.plugins` group) for discovery alongside the namespace package, enabling metadata (version, requires, description) without importing.
6. **Plugin metadata and dependency checks**: declared `requires`/`min_beets_version`, with clear, early error messages and a `beet plugins --check` diagnostic.
7. **Better fault containment**: wrap listener/stage invocation with per-plugin error handling, logging and optional disable-on-failure; add timing diagnostics to find slow plugins.
8. **Instance-scoped registry** (inject a plugin manager into a `Library`/session) to remove global state and simplify tests.
9. **Contract tests for providers**: a shared test suite any `MetadataSourcePlugin` must pass.
10. **Keep diagrams honest**: generate the plugin-inheritance diagram from source (introspection script in CI) so Task 3 type issues cannot recur.

## Priority suggestion
High value / low effort: (1) stable API docs, (3) typed events, (6) metadata and dependency checks, (10) generated diagrams.
