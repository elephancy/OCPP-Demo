import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "OCPP-Demo | EV Charging Operations Prototype",
  description: "Sign in to an OCPP 1.6 EV charging operations prototype with station lifecycle events, sessions, and messages.",
  icons: {
    icon: "/assets/brand/elephant-logo.ico",
    shortcut: "/assets/brand/elephant-logo.ico",
    apple: "/assets/brand/elephant-logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
