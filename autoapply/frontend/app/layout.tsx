import type { Metadata } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
// geist package: npm install geist  (NOT next/font/google)
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoApply — AI Job Application Agent",
  description:
    "Self-hostable AI that finds jobs, tailors your resume, and applies — all on your own infrastructure.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
