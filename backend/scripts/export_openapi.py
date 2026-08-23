"""Export the FastAPI OpenAPI schema as a committed JSON file.

Usage (from the backend directory)::

    uv run python scripts/export_openapi.py

The generated ``backend/openapi.json`` is consumed by ``openapi-typescript`` in
both ``frontend/`` and ``admin/``. Committing it means the CI drift check needs
no live backend.
"""

import json
import sys
from pathlib import Path


def main() -> None:
    _backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(_backend_root))
    from app.app import create_app  # import requires the path insert above

    app = create_app()
    schema = app.openapi()
    out = _backend_root / "openapi.json"
    out.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} ({len(json.dumps(schema))} bytes)")


if __name__ == "__main__":
    main()
