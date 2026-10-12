# Task 4 – Simplified plugin ↔ core diagram

Source: `docs/diagrams/plugin-core-interaction.puml` (component + class hybrid).

Design choices:
* Three layers only: **core**, **plugin API**, **extensions**.
* The registry/event bus is a single node, matching how beets really works (module functions, not a manager class).
* Concrete plugins are grouped as *providers* and *feature plugins* so the diagram does not depend on exact inheritance of individual plugins (see Task 3 caveats).
* Every arrow is one of: "loads", "sends events / asks for hooks", "specializes", or "uses core services".

Render with: `plantuml docs/diagrams/plugin-core-interaction.puml`
(not rendered in this environment: no PlantUML jar / network; syntax is plain component/class PlantUML).
