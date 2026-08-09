#!/usr/bin/env python3
"""Check that every feature model is registered in models_registry.py
and every feature router is wired in app.py. Non-zero exit on gaps."""

import sys
import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_APP = REPO_ROOT / "backend" / "app"
FEATURES_DIR = BACKEND_APP / "features"


def find_feature_files(directory: Path, pattern: str) -> list[str]:
    results = []
    for item in sorted(directory.iterdir()):
        if item.is_dir() and (item / pattern).exists():
            results.append(f"features/{item.name}/{pattern}")
    return results


def extract_class_names(file_path: Path) -> set[str]:
    try:
        tree = ast.parse(file_path.read_text())
        return {
            node.name
            for node in ast.iter_child_nodes(tree)
            if isinstance(node, ast.ClassDef)
        }
    except Exception:
        return set()


def check_models_registry() -> list[str]:
    errors = []
    registry_path = BACKEND_APP / "core" / "models_registry.py"
    registry_content = registry_path.read_text() if registry_path.exists() else ""

    model_files = find_feature_files(FEATURES_DIR, "models.py")
    for mf in model_files:
        feature_name = mf.split("/")[1]
        found = False
        actual_path = FEATURES_DIR / feature_name / "models.py"
        # Check the feature is imported in the registry
        if f"features.{feature_name}.models" in registry_content:
            found = True
        elif f"features.{feature_name}" in registry_content:
            # Check for specific model class imports
            classes = extract_class_names(actual_path)
            for cls in classes:
                if cls in registry_content:
                    found = True
                    break
        if not found:
            errors.append(f"UNREGISTERED_MODEL: app/features/{feature_name}/models.py")

    return errors


def check_router_registration() -> list[str]:
    errors = []
    app_py = BACKEND_APP / "app.py"
    if not app_py.exists():
        return ["APP_PY_NOT_FOUND"]
    app_content = app_py.read_text()

    for item in sorted(FEATURES_DIR.iterdir()):
        if not item.is_dir():
            continue
        feature_name = item.name
        endpoints_dir = item / "endpoints"
        if not endpoints_dir.is_dir():
            continue
        # Check the feature is mentioned in the router registration block
        if f"features.{feature_name}" not in app_content:
            errors.append(f"UNREGISTERED_ROUTER: features/{feature_name}")

    return errors


def main() -> int:
    model_errors = check_models_registry()
    router_errors = check_router_registration()

    errors = model_errors + router_errors

    if errors:
        for e in errors:
            print(f"  {e}")
        print(f"\n{len(errors)} registration error(s) found.")
        return 1

    print("All features registered.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
