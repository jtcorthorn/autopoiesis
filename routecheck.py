"""Read-only observations of declared entry -> map -> JSON routes. Standard library only."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import unquote


def contained(root, value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("path must be a nonempty relative POSIX path")
    rel = PurePosixPath(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("path escapes declared root")
    candidate = root.joinpath(*rel.parts)
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise ValueError("resolved path escapes declared root")
    return candidate


def mentions(text, source, target):
    # Check explicit literal references, not intent inferred from similar names.
    # Fenced examples and HTML comments are not routing declarations.
    text = re.sub(r"```[\s\S]*?```|<!--[\s\S]*?-->", "", text)
    text = unquote(text)
    parent = PurePosixPath(source).parent
    options = {target}
    try:
        options.add(str(PurePosixPath(target).relative_to(parent)))
    except ValueError:
        pass
    return any(re.search(r"(?<![\w/\\.-])" + re.escape(p) + r"(?![\w/\\.-])", text)
               for p in options)


def observe(root, manifest):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be an existing directory")
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise ValueError("unsupported manifest version")
    routes = manifest.get("routes")
    if not isinstance(routes, list) or not routes:
        raise ValueError("nonempty routes required; zero coverage is not success")
    ids = set()
    results = []
    for route in routes:
        if not isinstance(route, dict) or not isinstance(route.get("id"), str) or not route["id"]:
            raise ValueError("each route needs a nonempty id")
        if route["id"] in ids:
            raise ValueError("duplicate route id")
        ids.add(route["id"])
        keys = route.get("collections")
        if not isinstance(keys, list) or not keys or not all(isinstance(k, str) and k for k in keys):
            raise ValueError("explicit collection keys required")
        paths = {k: contained(root, route.get(k)) for k in ("entry", "map", "registry")}
        result = {"id": route["id"], "status": "PASS", "sources": {}, "counts": {}, "issues": []}
        data = {}
        try:
            for key, path in paths.items():
                raw = path.read_bytes()
                data[key] = raw.decode("utf-8-sig")
                result["sources"][key] = {"path": route[key], "sha256": hashlib.sha256(raw).hexdigest()}
            registry = json.loads(data["registry"])
            if not isinstance(registry, dict):
                raise ValueError("registry must be a JSON object")
            for key in keys:
                collection = registry.get(key)
                if not isinstance(collection, (dict, list)):
                    raise ValueError("missing or invalid collection: " + key)
                result["counts"][key] = len(collection)
            if not mentions(data["entry"], route["entry"], route["map"]):
                result["issues"].append("missing entry-to-map reference")
            if not mentions(data["map"], route["map"], route["registry"]):
                result["issues"].append("missing map-to-registry reference")
            if result["issues"]:
                result["status"] = "GAP"
        except (OSError, UnicodeError, ValueError) as exc:
            result["status"] = "INCOMPLETE"
            result["issues"].append(str(exc))
        results.append(result)
    status = "INCOMPLETE" if any(r["status"] == "INCOMPLETE" for r in results) else (
        "GAP" if any(r["status"] == "GAP" for r in results) else "PASS")
    return {"version": 1, "status": status, "coverage": len(results), "routes": results,
            "runtime_adoption": "not_measured", "writes": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
        report = observe(args.root, manifest)
    except (OSError, ValueError, TypeError) as exc:
        report = {"status": "INCOMPLETE", "error": str(exc), "writes": 0}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return {"PASS": 0, "GAP": 1, "INCOMPLETE": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
