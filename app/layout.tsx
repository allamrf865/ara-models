import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ARA Radar",
  description: "Advanced stock ranking and alert system",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
