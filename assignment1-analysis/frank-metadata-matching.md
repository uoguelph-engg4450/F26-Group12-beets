# Metadata Matching and Autotagging

## Subsystem Overview

The metadata matching and autotagging subsystem is responsible for identifying imported music and finding appropriate metadata for albums and individual tracks. During an import, Beets can compare the metadata already present in the user's files with candidate metadata from external sources such as MusicBrainz. The subsystem then evaluates these candidates and returns a recommendation indicating how confident Beets is in the match.

The main classes involved are located in the `beets.autotag` package. `Info` acts as the base metadata container, while `AlbumInfo` and `TrackInfo` extend it to represent album-level and track-level metadata. These objects contain the candidate metadata that the matching process evaluates.

The `Distance` class represents how different a candidate is from the user's existing metadata. A lower distance represents a closer match. Beets uses these distances to compare possible results rather than simply treating every candidate as either correct or incorrect. The matching system can therefore rank candidates and determine which result should be recommended.

## Main Class Relationships

The main inheritance relationships in the subsystem are straightforward. `AlbumInfo` and `TrackInfo` inherit from `Info`, while `AlbumMatch` and `TrackMatch` inherit from the more general `Match` class. This separates common matching behaviour from album-specific and track-specific results.

`AlbumMatch` represents a possible match for an entire album. One of its important responsibilities is maintaining a mapping between local library `Item` objects and candidate `TrackInfo` objects. It can also store unmatched local items and unmatched metadata tracks using `extra_items` and `extra_tracks`. This allows Beets to handle cases where the number or ordering of files does not perfectly match the candidate album.

`TrackMatch` represents the simpler case of matching an individual `Item` with a `TrackInfo` object. Both types of match are associated with a `Distance`, which expresses the quality of the match.

Candidate matches are collected into a `Proposal`. The proposal also contains a `Recommendation`, which indicates whether the best match is strong enough to accept or whether more input may be required.

## Interaction with the Importer

The autotagging subsystem is closely connected to the import process. By default, the Beets importer attempts to autotag newly imported music. During the import workflow, the importer requests metadata matches for either an album or an individual track. The matching subsystem evaluates available candidates and returns the results to the importer.

The importer can then use the recommendation to determine how to continue. Very close matches may be accepted automatically depending on the configuration, while less certain matches can be shown to the user for confirmation. Additionally, Beets allows autotagging to be disabled entirely, showing that the matching subsystem is a service used by the importer rather than being the importer itself.

## External Metadata Services

The matching process depends on external metadata providers to obtain candidate album and track information. MusicBrainz is the default metadata source in Beets, while additional metadata providers can be added through the plugin architecture.

This separation is important because the matching logic does not need to contain all of the code required to communicate with every external service. Instead, metadata providers return album and track information in the forms expected by the autotagging system, such as `AlbumInfo` and `TrackInfo`. The matching subsystem can then evaluate these candidates using the same matching logic regardless of where the metadata originated.

## Architectural Strengths

One strength of the subsystem is its separation of responsibilities. Metadata representation, match quality, candidate results, and recommendations are represented by different classes instead of being combined into one large class. This improves cohesion and makes the matching process easier to extend.

Another strength is that the system supports both album-level and single-track matching through the shared `Match` abstraction. The use of a `Distance` object also provides a flexible way to rank candidates instead of using a simple true-or-false matching approach.

The subsystem is also extensible because metadata can come from different providers. This reduces the dependency of the matching logic on a single external metadata service.

## Weaknesses and Possible Improvements

One weakness is that the matching process is spread across several modules, including `hooks.py`, `match.py`, `distance.py`, and `source.py`. Although this improves modularity, it can make the control flow more difficult to understand when first examining the code.

There is also coupling between the importer, autotagging subsystem, library models, and metadata providers. For example, `AlbumMatch` directly refers to library `Item` objects while also working with metadata `TrackInfo` objects. This is practical, but it means the matching layer is aware of both internal library objects and external metadata representations.

A possible improvement would be to introduce clearer interfaces between the importer, matching subsystem, and metadata providers. This could make dependencies more explicit and make the individual parts easier to test independently. Additional documentation describing the full path from importer request to metadata provider to final `Proposal` would also make the architecture easier to understand.