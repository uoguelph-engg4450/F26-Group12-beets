# Task 3 – Review of the generated plugin class diagrams

Files reviewed: `plugin-relationships.puml` (primary), `architecture.puml`,
`import-workflow.puml` (plugin touchpoints), plus `domain-relationships.puml` and
`matching-relationships.puml` for context. Originals are unchanged.

## What the diagrams get right
* `BeetsPlugin` → `MetadataSourcePlugin` → `SearchApiMetadataSourcePlugin<R>` specialization chain, with concrete plugins hanging off it.
* The note that the registry and event dispatcher are **module functions**, not a `PluginManager` class, is accurate and prevents a common misreading.
* `architecture.puml` correctly shows the bidirectional relationship between `beets.plugins` and `beetsplug.*` (core imports; plugins register back).
* Notes consistently state that diagrams are selected views, not exhaustive.

## Issues and suggested fixes

### Correctness to verify against source
1. **Concrete plugin parentage [verify].** `Acoustid --|> MetadataSourcePlugin` and `MusicBrainz/Spotify --|> SearchApiMetadataSourcePlugin` should be checked. Chroma historically extends `BeetsPlugin` directly (it contributes distance/candidates hooks); MusicBrainz may extend `MetadataSourcePlugin` rather than the Search API variant in some versions. Wrong inheritance edges are the biggest risk in this diagram.
2. **`TidalPlugin` [verify].** Confirm it exists in the targeted release; otherwise remove or replace with a plugin that certainly exists (e.g. `DiscogsPlugin`, `DeezerPlugin`).
3. **`Subcommand` stereotype.** Fine as `<<reference>>`, but `BeetsPlugin ..> Subcommand : commands() returns` is the only UI link; the CLI consumer (`beets.ui`) is absent from this diagram.

### Completeness gaps (extension points missing from `plugin-relationships.puml`)
* Template functions/fields, `item_types`/`album_types`, queries, `add_media_field`, distance hooks, and per-plugin `config` are listed only partially (template_* appear as members; the rest are absent).
* `beets.events` is mentioned in a note but not drawn.
* No consumer for the type/query/template extension points (`beets.library`/`dbcore`).
* `MetadataSourcePlugin` is shown, but its consumer (`beets.metadata_plugins` search orchestration → `beets.autotag`) is only an anonymous component.

### Notation and style
* `BeetsPlugin ..> Registry : register listener` and `Registry --> BeetsPlugin : _instances` form a cycle; clearer to label the first as `<<registers with>>` and keep the registry → plugin edge as the loaded-instance composition. Consider stereotyping `Registry` `<<module>>` (already done) and placing it centrally.
* Mixed dependency styles: `Stages`, `Search` are generic components; consider naming the real modules (`beets.importer`, `beets.autotag`) for traceability.
* `architecture.puml` header reads `@startuml Phase 1`, a leftover internal label that becomes the output file name; rename (e.g. `@startuml beets-architecture`).
* Files use CRLF line endings; normalize to LF (`.gitattributes`) to avoid noisy diffs.
* `plugin-relationships.puml` does not state which beets version it models; add a version note since the metadata-source layer changed recently.

### Cross-diagram consistency
* `architecture.puml` shows `providers ..> extensions` and `providers ..> plugins`; `plugin-relationships.puml` shows `Search ..> Registry` and `Search ..> MetadataSourcePlugin`. Same idea, different names ("providers" vs "Metadata search orchestration"); align naming.
* `import-workflow.puml` calls plugin touchpoints "early_import_stages and import_stages callbacks"; matches the plugin diagram members, which is good.

## Verdict
Good as a *conceptual* view; before it is treated as authoritative, confirm the three
inheritance/existence points in "Correctness to verify". The new diagram in Task 4
deliberately sticks to relationships that are stable across versions.
