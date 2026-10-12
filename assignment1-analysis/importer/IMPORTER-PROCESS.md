# Modelling the import subsystem

We started from the class diagram that pyreverse generated for the whole `beets` package. Its importer classes and inheritance relationships were correct, but it missed what explains the import. The links from a task to its candidate matches and to the autotagger were absent, because those attributes use union and sequence types that the tool did not resolve. It drew the session's reference to the library as aggregation, although the library exists independently of the session. It could not show the pipeline stages at all, because they are module-level functions rather than classes. The generated model also exposed a duplicate class: `ImportAbortError` is defined in both `session.py` and `tasks.py`, and the second definition is never used.

We corrected these relationships by reading the source. Our first hand-made diagrams included 27 classes and every branch of the workflow. When they were scaled to a page they were unreadable, and the sequence and activity diagrams showed the same flow twice. We therefore simplified them:

- The class diagram keeps the 16 classes needed to explain an import, with two to four key operations each and no parameter lists. Classes such as `ImportState`, `Distance` and the archive tasks are mentioned only in the text.
- The activity diagram shows the pipeline at the level of stages, in four swimlanes. Rarer branches (rescan, merge, upgrade and resume) are described in prose.
- The sequence diagram zooms in on a single interaction, metadata lookup and choice, so that it does not repeat the activity diagram. It is placed in the appendix to keep the subsystem section within two pages.

Two choices of notation needed care. Module functions such as `tag_album` were shown as a participant labelled "(module)" rather than as an invented class. Events were drawn as ordinary actions and synchronous messages rather than UML signals, because Beets delivers them synchronously and uses their return values.
