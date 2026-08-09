/**
 * Tile contract (conventions §Tile contract).
 *
 * Every Phase 2 content feature contributes one tile as its final sub-task.
 * The homepage grid renders overview intros full-width at top, tiles below,
 * filtered client-side by audience relevance. Omission, not dimming.
 */

// === APPEND-ZONE-START: tile registrations ===
// Add new tiles below, alphabetical by id, never reorder
// "projects" tile — registered in frontend/components/tiles/ProjectsTile.tsx
// === APPEND-ZONE-END: tile registrations ===

export interface Tile {
  id: string;
  title: string;
  summary: string;
  href: string;
  /** Which audiences see this tile (empty = all audiences). */
  audiences: string[];
  /** Higher = earlier in the grid. */
  priority: number;
  /** When true the tile is omitted from the grid entirely. */
  isEmpty: boolean;
}
