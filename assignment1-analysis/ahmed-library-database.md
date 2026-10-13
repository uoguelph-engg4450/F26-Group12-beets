# Core library and database

**ENGG 4450 — Assignment 1: Reverse Engineering**  
**Prepared by:** Ahmed, Member 2  
**Subsystem:** Beets music library and database  
**Source reviewed:** `beets/library/library.py`, `beets/library/models.py`, and `beets/dbcore/db.py`

## Responsibility and structure

The music library connects Beets’ music-specific records to its persistence layer. `Library` extends the general `dbcore.Database` and registers `Item` and `Album` as its database models. `LibModel` extends the generic `dbcore.Model[Library]` with functionality shared by both record types. `Item` represents a song or track; `Album` represents an album record. Their inheritance chain separates general database behavior from music-specific behavior while allowing both records to share library fields, formatting, plugin fields, and persistence operations.

The diagram [ahmed-library-database.puml](ahmed-library-database.puml) shows the main classes and their relationships. It is a simplified view of the relevant source, rather than a complete class inventory.

## How records are stored and retrieved

`Album` and `Item` use separate main tables (`albums` and `items`) and separate flexible-attribute tables. The base `Model` presents fixed, flexible, and computed fields through a uniform mapping and attribute interface. Fixed fields are backed by table columns; flexible fields can store additional metadata; computed fields can be supplied by plugins. `Item` also indexes `album_id` for album-related lookups. The database layer wraps SQLite and provides transactions for database operations.

`Library.add_album(items)` builds an album using selected metadata from the first item, adds it to the database, assigns its new ID to each item’s `album_id`, and adds or stores each item inside a transaction. The library’s `items()` and `albums()` methods parse a query and return `Results` from the database layer. A `Results` object retains its database and query context, constructs model objects lazily as rows are consumed, and caches objects already materialized. This avoids eagerly constructing every returned record and makes repeat iteration cheaper. See `beets/library/library.py` (`add_album`, `_fetch`, `items`, `albums`) and `beets/dbcore/db.py` (`Model`, `Results`, `Transaction`, `Database._get_results`).

The album–track relationship is represented by `Item.album_id`. An item can have `album_id=None`, so a track may exist as a singleton; when an album ID is present, `Album.items()` queries for items with that ID. Consequently an album can have zero or more matching tracks, while any item has zero or one album. This is a logical relationship implemented through the ID and queries; the diagram does not claim that SQLite enforces a foreign-key constraint. `Album.remove(with_items=False)` can delete the album while retaining its items. The current method does not clear those items’ `album_id`, so the retained items can point at an album that no longer exists. This is a referential-consistency edge case worth documenting and considering in a future improvement.

## Design assessment

The model/database split gives albums and tracks common persistence and field behavior without placing every concern in `Library`. Transactions group the album and item writes, helping keep album creation together. `Results` defers object construction, and the album membership index supports the corresponding lookup. Flexible fields also let the library represent metadata beyond the fixed schema.

One interface inconsistency appears in `Album.items()`: it conflicts by name with the inherited `Model.items()` interface. The source explicitly says this album-specific method predates the base method and remains for plugin compatibility. Keeping the method avoids breaking existing consumers, though it makes the same method name mean different things at the album and model levels. Another limitation is the stale `album_id` possible when removing an album but keeping its tracks. A concrete improvement would be to define and enforce a detach policy for that operation—for example, clear and store each retained item’s album reference in the same transaction as album deletion—and add a regression test for it. The resulting behavior should be documented for plugin users.

## Source references

- `beets/library/library.py`: `Library`, `_models`, `add_album`, `_fetch`, `items`, `albums`, and `get_album`.
- `beets/library/models.py`: `LibModel`, `Album.items`, `Album.remove`, `Item.album_id`, and `Item.get_album`.
- `beets/dbcore/db.py`: `Model`, `Results`, `Transaction`, and `Database` query/persistence operations.
