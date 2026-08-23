"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  siteKey: string;
  consentText: string;
}

interface TurnstileApi {
  render: (el: HTMLElement, opts: { sitekey: string; callback: () => void }) => string;
  getResponse: (id: string) => string;
  reset: (id?: string) => void;
}

function turnstile(): TurnstileApi | undefined {
  return (window as unknown as { turnstile?: TurnstileApi }).turnstile;
}

export default function ContactForm({ siteKey, consentText }: Props) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success">("idle");
  const [error, setError] = useState("");
  const turnstileRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string>("");

  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      const w = turnstile();
      if (w && turnstileRef.current) {
        widgetId.current = w.render(turnstileRef.current, {
          sitekey: siteKey,
          callback: () => {},
        });
      }
    };
    document.head.appendChild(script);
    return () => {
      document.head.removeChild(script);
    };
  }, [siteKey]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setStatus("submitting");

    let token = "";
    try {
      const w = turnstile();
      if (w && widgetId.current) {
        token = w.getResponse(widgetId.current);
        if (!token) {
          setError("Please complete the verification challenge.");
          setStatus("idle");
          return;
        }
      }
    } catch {
      setError("Verification challenge not available. Please refresh.");
      setStatus("idle");
      return;
    }

    try {
      await fetch("/api/v1/forms/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          message: message.trim(),
          consent_given: true,
          consent_text: consentText,
          turnstile_token: token,
          _hpt: "",
        }),
      });

      setStatus("success");
    } catch {
      setError("Something went wrong. Please try again.");
      setStatus("idle");
    } finally {
      try {
        const w = turnstile();
        if (w && widgetId.current) w.reset(widgetId.current);
      } catch {}
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Honeypot hidden field */}
      <input
        type="text"
        name="_hpt"
        tabIndex={-1}
        autoComplete="off"
        aria-hidden="true"
        style={{ position: "absolute", left: "-9999px", opacity: 0 }}
        onChange={() => {}}
      />

      <div>
        <label htmlFor="cf-name" className="block text-sm font-medium mb-1.5">
          Name
        </label>
        <input
          id="cf-name"
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="Your name"
        />
      </div>

      <div>
        <label htmlFor="cf-email" className="block text-sm font-medium mb-1.5">
          Email
        </label>
        <input
          id="cf-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          placeholder="you@example.com"
        />
      </div>

      <div>
        <label htmlFor="cf-message" className="block text-sm font-medium mb-1.5">
          Message
        </label>
        <textarea
          id="cf-message"
          required
          rows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-y"
          placeholder="Your message..."
        />
      </div>

      <div
        ref={turnstileRef}
        data-sitekey={siteKey}
        className="cf-turnstile"
      />

      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}

      {status === "success" ? (
        <p className="text-sm text-green-600 font-medium">
          Thank you for your message. I&apos;ll get back to you.
        </p>
      ) : (
        <button
          type="submit"
          disabled={status === "submitting"}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {status === "submitting" ? "Sending..." : "Send Message"}
        </button>
      )}
    </form>
  );
}
