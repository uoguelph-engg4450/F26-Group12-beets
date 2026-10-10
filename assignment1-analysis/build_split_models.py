"""Build traceable, names-only UML coverage views from the static inventory."""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
classes = data["classes"]
by_id = {c["id"]: c for c in classes}
groups = defaultdict(list)
query_logic = {"Query", "CollectionQuery", "MutableCollectionQuery", "AndQuery", "OrQuery", "NotQuery", "TrueQuery", "FalseQuery"}
core_titles = {
    "01-library": "Music library and domain models",
    "02-database": "Database, transactions, results and model support",
    "03-query-predicates": "Field predicates, date values and parsing errors",
    "04-query-combinations": "Query combinations",
    "05-field-types": "Database field types",
    "06-sorting": "Sorting strategies",
    "07-migrations": "Library schema migrations",
    "08-importer": "Import sessions, tasks, archives, actions and state",
    "09-autotag": "Metadata values, matching and distance",
    "10-plugin-contracts": "Plugin and metadata source contracts",
    "11-cli": "CLI commands, parsers and import presentation",
    "12-events": "Typed event payload schemas",
    "13-support": "Configuration, logging and shared utilities",
    "14-art-resizing": "Artwork resizing backends",
    "15-templates": "Template parsing and evaluation",
    "16-pipeline": "Pipeline and worker threads",
}


def owner(c):
    m, scope = c["module"], c["scope"]
    if scope == "core":
        if m == "beets.library.migrations":
            return "core/07-migrations"
        if m.startswith("beets.library"):
            return "core/01-library"
        if m == "beets.dbcore.db":
            return "core/02-database"
        if m == "beets.dbcore.query":
            return "core/04-query-combinations" if c["name"] in query_logic else "core/03-query-predicates"
        if m == "beets.dbcore.types":
            return "core/05-field-types"
        if m == "beets.dbcore.sort":
            return "core/06-sorting"
        if m.startswith("beets.importer"):
            return "core/08-importer"
        if m.startswith("beets.autotag"):
            return "core/09-autotag"
        if m in {"beets.plugins", "beets.metadata_plugins"}:
            return "core/10-plugin-contracts"
        if m.startswith("beets.ui"):
            return "core/11-cli"
        if m == "beets.events":
            return "core/12-events"
        if m == "beets.util.artresizer":
            return "core/14-art-resizing"
        if m == "beets.util.functemplate":
            return "core/15-templates"
        if m == "beets.util.pipeline":
            return "core/16-pipeline"
        return "core/13-support"
    if scope in {"docs", "extra"}:
        return "support/documentation-and-release"
    return scope + "/" + m.replace(".", "-")


for c in classes:
    groups[owner(c)].append(c)

pages = {}
for group, records in sorted(groups.items()):
    records.sort(key=lambda c: (c["file"], c["line"]))
    # Preserve intentional core groupings; paginate appendices at 20 owned classes.
    limit = 24 if group.startswith("core/") else 20
    chunks = [records[i:i + limit] for i in range(0, len(records), limit)]
    for index, chunk in enumerate(chunks, 1):
        key = group + (f"-{index:02}" if len(chunks) > 1 else "")
        pages[key] = chunk

owned = {c["id"]: key for key, records in pages.items() for c in records}
aliases = {c["id"]: f"c_{index:04}" for index, c in enumerate(classes)}
memberships = []
index = ["# UML model index", "", "Each source declaration has one home view. Referenced base classes may also appear in other views with `<<reference>>`. These are names-only coverage and inheritance views; curated relationship models are separate.", "", "| View | Owned classes |", "| --- | ---: |"]


def stereotype(c):
    def ancestors(cid, seen=None):
        seen = set() if seen is None else seen
        if cid in seen:
            return []
        seen.add(cid)
        bases = list(by_id[cid]["bases"])
        for relation in data["inheritance"]:
            if relation["child"] == cid and relation["internal"]:
                bases += ancestors(relation["parent"], seen)
        return bases
    bases = " ".join(ancestors(c["id"]))
    if "TypedDict" in bases or c["form"] == "factory:TypedDict":
        return "schema"
    if "Protocol" in bases:
        return "protocol"
    if "NamedTuple" in bases or c["form"] in {"factory:namedtuple", "factory:NamedTuple"}:
        return "namedtuple"
    if "Enum" in bases:
        return "enum"
    if c["lexical_scope"]:
        return "nested"
    return ""


for key, records in pages.items():
    path = HERE / "models" / (key + ".puml")
    path.parent.mkdir(parents=True, exist_ok=True)
    title = core_titles.get(key.split("/")[-1], key.replace("/", " / "))
    lines = ["@startuml", "set namespaceSeparator none", "hide empty members", "skinparam classAttributeIconSize 0", "left to right direction", "title " + title]
    present = {c["id"] for c in records}
    for module in sorted({c["module"] for c in records}):
        lines.append(f'package "{module}" {{')
        for c in records:
            if c["module"] != module:
                continue
            lines.append(f"  ' {c['id']} at {c['file']}:{c['line']}")
            tag = stereotype(c)
            keyword = "abstract class" if c["abstract_methods"] else "class"
            lines.append(f'  {keyword} "{c["name"]}" as {aliases[c["id"]]}' + (f" <<{tag}>>" if tag else ""))
            memberships.append({"class_id": c["id"], "scope": c["scope"], "home_model": "models/" + key + ".puml", "source_file": c["file"], "line": c["line"]})
        lines.append("}")
    reference_aliases = {}
    relevant = [r for r in data["inheritance"] if r["child"] in present]
    parents = sorted({r["parent"] for r in relevant} - present)
    for number, parent in enumerate(parents):
        alias = aliases[parent] if parent in aliases else f"external_{number}"
        reference_aliases[parent] = alias
        lines.append(f'class "{parent}" as {alias} <<' + ("reference" if parent in aliases else "external") + ">>")
    for r in relevant:
        parent_alias = aliases[r["parent"]] if r["parent"] in present else reference_aliases[r["parent"]]
        lines.append(f'{aliases[r["child"]]} --|> {parent_alias}')
        if "[" in r["base_expression"]:
            lines.append("' Parameterized source base: " + r["base_expression"])
    lines += ["legend bottom", "Owned classes are inside module packages.", "reference = declared in another home view; external = external or unresolved base.", "schema/protocol/namedtuple describe Python typing constructs.", "This view shows declarations and direct bases; consult the curated models for associations.", "endlegend", "@enduml", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    index.append(f"| [{key}](models/{key}.puml) | {len(records)} |")

with (HERE / "model-membership.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["class_id", "scope", "home_model", "source_file", "line"])
    writer.writeheader()
    writer.writerows(memberships)
(HERE / "MODEL-INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
catalog = ["# Complete class catalog", "", "One row per source declaration, including nested classes and the two functional TypedDict schemas. Bases are the literal source expressions. See inheritance.csv for resolved names.", "", "| Class | Source | Direct bases | Home UML model |", "| --- | --- | --- | --- |"]
for c in sorted(classes, key=lambda c: c["id"]):
    source = "../F26-Group12-beets/" + c["file"]
    model = "models/" + owned[c["id"]] + ".puml"
    bases = ", ".join(c["bases"]).replace("|", "&#124;") or "(implicit object)"
    catalog.append(f"| `{c['id']}` | [{c['file']}:{c['line']}]({source}) | `{bases}` | [{owned[c['id']]}]({model}) |")
(HERE / "CLASS-CATALOG.md").write_text("\n".join(catalog) + "\n", encoding="utf-8")

assert len(memberships) == len(classes)
assert len(owned) == len(classes)
assert set(owned) == set(by_id)
for key, records in pages.items():
    content = (HERE / "models" / (key + ".puml")).read_text(encoding="utf-8")
    assert content.count("@startuml") == content.count("@enduml") == 1
    for c in records:
        assert f"as {aliases[c['id']]}" in content
    declared = set(re.findall(r"\bas (\w+)", content))
    for a, b in re.findall(r"^(\w+) --\|> (\w+)$", content, re.M):
        assert a in declared and b in declared
validation = {"owned_classes": len(owned), "model_count": len(pages), "unassigned_classes": [], "duplicate_home_assignments": [], "undeclared_inheritance_endpoints": [], "rendered": False, "models_by_scope": {scope: sum(key.startswith(scope + '/') for key in pages) for scope in ['core', 'plugins', 'test-support', 'test', 'support']}, "core_models": {key: len(records) for key, records in pages.items() if key.startswith('core/')}}
(HERE / "coverage-validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
print(json.dumps(validation, indent=2))
