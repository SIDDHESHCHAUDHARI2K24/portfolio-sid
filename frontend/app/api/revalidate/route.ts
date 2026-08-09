import { timingSafeEqual } from "node:crypto";

import { revalidateTag } from "next/cache";

const SECRET_HEADER = "x-revalidation-secret";

function secretIsValid(provided: string | null): boolean {
  const expected = process.env.REVALIDATION_SECRET;
  if (!expected || !provided) {
    return false;
  }
  const providedBytes = Buffer.from(provided);
  const expectedBytes = Buffer.from(expected);
  if (providedBytes.length !== expectedBytes.length) {
    return false;
  }
  return timingSafeEqual(providedBytes, expectedBytes);
}

export async function POST(request: Request) {
  if (!secretIsValid(request.headers.get(SECRET_HEADER))) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const tags: unknown =
    typeof body === "object" && body !== null
      ? (body as { tags?: unknown }).tags
      : undefined;
  if (
    !Array.isArray(tags) ||
    tags.length === 0 ||
    !tags.every((tag) => typeof tag === "string" && tag.length > 0)
  ) {
    return Response.json(
      { error: 'Body must be {"tags": ["<tag>", ...]}' },
      { status: 400 },
    );
  }

  for (const tag of tags) {
    // Next 16: single-arg revalidateTag is deprecated; { expire: 0 } is the
    // sanctioned webhook pattern for external systems needing immediate expiry.
    revalidateTag(tag, { expire: 0 });
  }

  return Response.json({ revalidated: true, tags });
}
