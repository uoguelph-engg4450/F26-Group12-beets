"""Static source/PlantUML audit; does not import or execute repository code."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "F26-Group12-beets"
OUT = Path(__file__).resolve().parent


def module_name(path):
    parts = list(path.relative_to(ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def scope_of(module):
    if module.startswith("beets.test"):
        return "test-support"
    if module.startswith("beetsplug"):
        return "plugins"
    if module.startswith("beets"):
        return "core"
    return module.split(".")[0]


def expression(node):
    return ast.unparse(node) if node is not None else ""


class Collector(ast.NodeVisitor):
    def __init__(self, path, tree):
        self.path, self.module, self.tree = path, module_name(path), tree
        self.stack, self.context, self.classes, self.imports = [], [], [], {}
        self.import_edges = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports[alias.asname or alias.name.split(".")[0]] = (
                alias.name if alias.asname else alias.name.split(".")[0]
            )
            self.import_edges.append((alias.name, " / ".join(self.context), node.lineno))

    def visit_ImportFrom(self, node):
        package = self.module if self.path.name == "__init__.py" else self.module.rpartition(".")[0]
        parts = package.split(".")
        if node.level:
            prefix = ".".join(parts[:len(parts) - node.level + 1])
            origin = ".".join(x for x in (prefix, node.module) if x)
        else:
            origin = node.module or ""
        for alias in node.names:
            if alias.name != "*":
                self.imports[alias.asname or alias.name] = f"{origin}.{alias.name}"
                self.import_edges.append((f"{origin}.{alias.name}", " / ".join(self.context), node.lineno))

    def visit_If(self, node):
        self.context.append("if " + expression(node.test))
        for child in node.body:
            self.visit(child)
        self.context.pop()
        self.context.append("else " + expression(node.test))
        for child in node.orelse:
            self.visit(child)
        self.context.pop()

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        record = {
            "id": ".".join([self.module, *self.stack, node.name]),
            "name": node.name, "module": self.module,
            "file": self.path.relative_to(ROOT).as_posix(), "line": node.lineno,
            "scope": scope_of(self.module), "lexical_scope": ".".join(self.stack),
            "context": " / ".join(self.context), "form": "class",
            "bases": [expression(n) for n in node.bases],
            "metaclass": next((expression(k.value) for k in node.keywords if k.arg == "metaclass"), ""),
            "decorators": [expression(n) for n in node.decorator_list],
            "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
            "abstract_methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and any("abstractmethod" in expression(d) for d in n.decorator_list)],
            "fields": [], "signatures": [], "assignments": [],
        }
        # Walk the class body, excluding nested classes and functions inside methods.
        def walk(nodes, method=None):
            for child in nodes:
                if isinstance(child, ast.ClassDef):
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if method is not None:
                        continue
                    for arg in [*child.args.posonlyargs, *child.args.args, *child.args.kwonlyargs]:
                        if arg.annotation:
                            record["signatures"].append((child.name + "." + arg.arg, expression(arg.annotation), arg.lineno))
                    if child.returns:
                        record["signatures"].append((child.name + ".return", expression(child.returns), child.lineno))
                    walk(child.body, child.name)
                    continue
                if isinstance(child, ast.AnnAssign):
                    target = expression(child.target)
                    if method is None or target.startswith("self."):
                        record["fields"].append((target.removeprefix("self."), expression(child.annotation), child.lineno))
                if isinstance(child, (ast.Assign, ast.AnnAssign)) and child.value is not None:
                    targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                    for target in targets:
                        name = expression(target)
                        if method is None or name.startswith("self."):
                            record["assignments"].append((name.removeprefix("self."), expression(child.value), child.lineno))
                walk(list(ast.iter_child_nodes(child)), method)
        walk(node.body)
        self.classes.append(record)
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            factory = expression(node.value.func).split(".")[-1]
            if factory in {"TypedDict", "NamedTuple", "namedtuple"}:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.classes.append({
                            "id": ".".join([self.module, *self.stack, target.id]),
                            "name": target.id, "module": self.module,
                            "file": self.path.relative_to(ROOT).as_posix(), "line": node.lineno,
                            "scope": scope_of(self.module), "lexical_scope": ".".join(self.stack),
                            "context": " / ".join(self.context), "form": "factory:" + factory,
                            "bases": [factory], "metaclass": "", "decorators": [],
                            "methods": [], "abstract_methods": [], "fields": [], "signatures": [], "assignments": [],
                        })
                        if len(node.value.args) > 1 and isinstance(node.value.args[1], ast.Dict):
                            self.classes[-1]["fields"] = [(str(k.value), expression(v), node.lineno) for k, v in zip(node.value.args[1].keys, node.value.args[1].values) if isinstance(k, ast.Constant)]
        self.generic_visit(node)


collectors, errors = {}, []
for path in sorted(ROOT.rglob("*.py")):
    if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
        continue
    try:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    except (SyntaxError, UnicodeError) as exc:
        errors.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})
        continue
    collector = Collector(path, tree)
    collector.visit(tree)
    collectors[collector.module] = collector

classes = [record for c in collectors.values() for record in c.classes]
by_id = {record["id"]: record for record in classes}
modules = set(collectors)


def resolve(symbol, module, lexical="", seen=None):
    seen = set() if seen is None else seen
    key = (symbol, module, lexical)
    if key in seen:
        return symbol
    seen.add(key)
    if symbol in by_id or symbol in modules:
        return symbol
    for prefix in [lexical, ""] if lexical else [""]:
        candidate = ".".join(x for x in (module, prefix, symbol) if x)
        if candidate in by_id:
            return candidate
    first, _, rest = symbol.partition(".")
    if module in collectors and first in collectors[module].imports:
        mapped = collectors[module].imports[first] + ("." + rest if rest else "")
        if mapped != symbol:
            if mapped in by_id or mapped in modules:
                return mapped
            # Follow exports through the longest known module prefix.
            for i in range(len(mapped.split(".")) - 1, 0, -1):
                origin = ".".join(mapped.split(".")[:i])
                tail = ".".join(mapped.split(".")[i:])
                if origin in collectors:
                    return resolve(tail, origin, seen=seen)
            return mapped
    for i in range(len(symbol.split(".")) - 1, 0, -1):
        origin = ".".join(symbol.split(".")[:i])
        if origin in collectors:
            return resolve(".".join(symbol.split(".")[i:]), origin, seen=seen)
    return symbol


inheritance, references = [], []
for record in classes:
    for base in record["bases"]:
        node = ast.parse(base, mode="eval").body
        raw = expression(node.value if isinstance(node, ast.Subscript) else node)
        resolved = resolve(raw, record["module"], record["lexical_scope"])
        inheritance.append({"child": record["id"], "base_expression": base, "parent": resolved,
                            "internal": resolved in by_id, "file": record["file"], "line": record["line"]})
    for kind in ("fields", "signatures"):
        for member, annotation, line in record[kind]:
            try:
                node = ast.parse(annotation, mode="eval")
                if isinstance(node.body, ast.Constant) and isinstance(node.body.value, str):
                    node = ast.parse(node.body.value, mode="eval")
                symbols = {expression(n) for n in ast.walk(node) if isinstance(n, (ast.Name, ast.Attribute))}
            except SyntaxError:
                continue
            for symbol in symbols:
                target = resolve(symbol, record["module"], record["lexical_scope"])
                if target in by_id:
                    references.append({"source": record["id"], "target": target, "kind": "field" if kind == "fields" else "signature",
                                       "member": member, "annotation": annotation, "file": record["file"], "line": line})

puml = (ROOT / "classes_Beets.puml").read_text(encoding="utf-8-sig")
diagram_ids = set(re.findall(r'^class "[^"]+" as ([\w.]+)', puml, re.M))
relationships = []
for line_number, line in enumerate(puml.splitlines(), 1):
    match = re.match(r"^([\w.]+)\s+(--\|>|-->|--\*|--o|\.\.>)\s+([\w.]+)(?:\s*:\s*(.*))?$", line)
    if match:
        source, arrow, target, label = match.groups()
        relationships.append({"source": source, "arrow": arrow, "target": target, "label": label or "", "line": line_number})
actual_inheritance = {(r["child"], r["parent"]) for r in inheritance if r["internal"]}
diagram_inheritance = {(r["source"], r["target"]) for r in relationships if r["arrow"] == "--|>"}
both = set(by_id) & diagram_ids
package_puml = (ROOT / "packages_Beets.puml").read_text(encoding="utf-8-sig")
package_ids = set(re.findall(r'^package "[^"]+" as ([\w.]+)', package_puml, re.M))
package_relations = re.findall(r"^([\w.]+) (\.\.>|-->) ([\w.]+)", package_puml, re.M)
package_edges = {(a, b) for a, _, b in package_relations}
source_imports = []
for module, collector in collectors.items():
    for symbol, context, line in collector.import_edges:
        candidates = [symbol] + [".".join(symbol.split(".")[:i]) for i in range(len(symbol.split(".")) - 1, 0, -1)]
        target = next((candidate for candidate in candidates if candidate in modules), "")
        if target and target != module:
            source_imports.append({"source": module, "target": target, "context": context, "line": line})
source_package_edges = {(r["source"], r["target"]) for r in source_imports}
audit = {
    "input_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ["classes_Beets.puml", "packages_Beets.puml"]},
    "python_files": len(collectors), "parse_errors": errors,
    "class_declarations": len(classes), "unique_class_ids": len(by_id),
    "class_forms": dict(Counter(r["form"] for r in classes)),
    "classes_by_scope": dict(Counter(r["scope"] for r in classes)),
    "files_by_scope": dict(Counter(scope_of(m) for m in collectors)),
    "diagram_class_declarations": len(re.findall(r'^class ', puml, re.M)),
    "diagram_class_ids": len(diagram_ids), "diagram_relationship_counts": dict(Counter(r["arrow"] for r in relationships)),
    "diagram_covered_by_scope": dict(Counter(by_id[c]["scope"] for c in both)),
    "missing_class_ids": sorted(set(by_id) - diagram_ids), "extra_class_ids": sorted(diagram_ids - set(by_id)),
    "missing_inheritance_between_diagram_classes": sorted(actual_inheritance - diagram_inheritance & {(a, b) for a, b in actual_inheritance if a in both and b in both}),
    "unsupported_diagram_inheritance": sorted(diagram_inheritance - actual_inheritance),
    "internal_inheritance_count": len(actual_inheritance), "external_base_expressions": sum(not r["internal"] for r in inheritance),
    "metaclasses": [{"id": r["id"], "metaclass": r["metaclass"]} for r in classes if r["metaclass"]],
    "diagram_package_count": len(package_ids), "diagram_package_edge_count": len(package_edges),
    "diagram_package_arrow_counts": dict(Counter(arrow for _, arrow, _ in package_relations)),
    "packages_missing": sorted(modules - package_ids), "packages_extra": sorted(package_ids - modules),
    "source_import_edge_count": len(source_package_edges),
    "missing_import_edges_between_diagram_modules": sorted((source_package_edges - package_edges) & {(a, b) for a, b in source_package_edges if a in package_ids and b in package_ids}),
    "diagram_edges_without_direct_import": sorted(package_edges - source_package_edges),
    "diagram_relationships": relationships,
}

OUT.mkdir(exist_ok=True)
(OUT / "inventory.json").write_text(json.dumps({"classes": classes, "inheritance": inheritance, "typed_references": references, "imports": source_imports}, indent=2), encoding="utf-8")
(OUT / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")


def write_csv(name, rows, columns):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: " | ".join(v) if isinstance(v, list) else v for k, v in row.items() if k in columns})


write_csv("class-inventory.csv", classes, ["id", "scope", "file", "line", "form", "context", "lexical_scope", "bases", "metaclass", "methods", "abstract_methods"])
write_csv("inheritance.csv", inheritance, ["child", "parent", "base_expression", "internal", "file", "line"])
write_csv("typed-references.csv", references, ["source", "target", "kind", "member", "annotation", "file", "line"])
write_csv("module-imports.csv", source_imports, ["source", "target", "context", "line"])
summary = {k: v for k, v in audit.items() if not isinstance(v, list)}
summary["missing_class_count"] = len(audit["missing_class_ids"])
summary["extra_class_count"] = len(audit["extra_class_ids"])
summary["missing_package_count"] = len(audit["packages_missing"])
print(json.dumps(summary, indent=2))
print("Missing core:", [c for c in audit["missing_class_ids"] if by_id[c]["scope"] == "core"])
print("Unsupported inheritance:", audit["unsupported_diagram_inheritance"])
print("Missing inheritance among covered classes:", audit["missing_inheritance_between_diagram_classes"])
