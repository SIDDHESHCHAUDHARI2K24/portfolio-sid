/**
 * Relevance resolver — mirrors ``backend/app/features/relevance/service.py:is_relevant``.
 *
 * Conventions invariant 10: two implementations (Python + TypeScript), both pure.
 * A shared fixture asserts identical outputs; drift fails CI.
 */

export function isRelevant(
  itemTagSlugs: Set<string>,
  overrides: Set<string>,
  audience: string,
  tagMap: Record<string, Set<string>>,
): boolean {
  if (overrides.has(audience)) return true;
  const audienceTags = tagMap[audience] ?? new Set<string>();
  return audienceTags.size > 0 && itemTagSlugs.intersection(audienceTags).size > 0;
}
