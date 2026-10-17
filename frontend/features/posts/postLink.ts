export type PostLinkInput = {
  platform: string;
  slug?: string | null;
  url?: string | null;
};

/**
 * Internal posts open on this site (same tab); every other platform is an
 * outbound link (new tab).
 */
export function postHref(post: PostLinkInput): { href: string; external: boolean } {
  if (post.platform === "internal") {
    return { href: post.slug ? `/writing/${post.slug}` : "#", external: false };
  }
  return { href: post.url ?? "#", external: true };
}
