import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { CategoryProvider } from "@/components/CategoryProvider";
import { IntroOverlay } from "@/components/intro";
import { AudioProvider } from "@/components/audio";
import HUD from "@/components/hud/HUD";
import { buildRootMetadata } from "@/lib/metadata";

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = buildRootMetadata();

export default function RootLayout({ children }: LayoutProps<"/">) {
  const token = process.env.NEXT_PUBLIC_CF_BEACON_TOKEN

  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        {token && (
          <script
            defer
            src="https://static.cloudflarestorage.com/beacon.min.js"
            data-cf-beacon={`{"token": "${token}"}`}
          />
        )}
      </head>
      <body className="min-h-full flex flex-col">
        <CategoryProvider>
          <AudioProvider>
            <IntroOverlay />
            {children}
            <HUD />
          </AudioProvider>
        </CategoryProvider>
      </body>
    </html>
  );
}
