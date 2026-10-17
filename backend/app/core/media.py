"""``/media`` static mount with Cache-Control matched to key naming.

Keys written via ``content_hashed_key`` (``<prefix>-<12 hex>.<ext>``) can never
change bytes under the same name, so they are cached for a year. Any other key
may be overwritten in place and gets a short cache. Errors get no cache header.
"""

import re

from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from app.core.storage import CACHE_CONTROL

SHORT_CACHE_CONTROL = "public, max-age=300"
_HASHED_KEY = re.compile(r"-[0-9a-f]{12}\.[A-Za-z0-9]+$")


def cache_control_for(path: str) -> str:
    return CACHE_CONTROL if _HASHED_KEY.search(path) else SHORT_CACHE_CONTROL


class MediaStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code in (200, 206, 304):
            response.headers["Cache-Control"] = cache_control_for(path)
        return response
