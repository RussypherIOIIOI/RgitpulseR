import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import "./globals.css";

// TMC type stack, self-hosted (SIL OFL 1.1). The CSS maps these variables onto the
// brand roles: display (Poppins), body (Lora), label (Space Grotesk), signal (Matrix Sans).
const Poppins = localFont({ src: "./fonts/poppins-latin-600-normal.woff2", weight: "600",
  variable: "--font-poppins", display: "swap" });
const Lora = localFont({ src: [
  { path: "./fonts/lora-latin-400-normal.woff2", weight: "400", style: "normal" },
  { path: "./fonts/lora-latin-600-normal.woff2", weight: "600", style: "normal" },
], variable: "--font-lora", display: "swap", adjustFontFallback: "Times New Roman" });
const SpaceGrotesk = localFont({ src: [
  { path: "./fonts/space-grotesk-latin-400-normal.woff2", weight: "400", style: "normal" },
  { path: "./fonts/space-grotesk-latin-500-normal.woff2", weight: "500", style: "normal" },
], variable: "--font-space-grotesk", display: "swap" });
const MatrixSans = localFont({ src: "./fonts/MatrixSans-Regular.woff2", weight: "400",
  variable: "--font-matrix-sans", display: "swap", adjustFontFallback: false });

export const metadata: Metadata = {
  title: "GitPulse | Repository observatory · The Meredith Collective",
  description: "Explainable merge times, issue ages and weekly throughput for one GitHub repository, published from a single validated PostgreSQL snapshot. A portfolio project from The Meredith Collective.",
  applicationName: "GitPulse",
  openGraph: {
    title: "GitPulse: GitHub activity, published as numbers you can explain",
    description: "Python imports, a PostgreSQL snapshot and a Next.js dashboard for one repository's issues and pull requests.",
    siteName: "The Meredith Collective",
    type: "website",
  },
};

export const viewport: Viewport = { themeColor: "#08070d", colorScheme: "dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" className={`${Poppins.variable} ${Lora.variable} ${SpaceGrotesk.variable} ${MatrixSans.variable}`}>
    <body>{children}</body>
  </html>;
}
