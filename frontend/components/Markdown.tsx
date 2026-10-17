import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Server-rendered markdown for native articles: GFM only, NO rehype-raw, so raw
 * HTML in the body is never turned into elements (React escapes it as visible
 * text) and react-markdown's default urlTransform strips unsafe link protocols.
 */
export default function Markdown({ body }: { body: string }) {
  return (
    <div className="article-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {body}
      </ReactMarkdown>
    </div>
  );
}
