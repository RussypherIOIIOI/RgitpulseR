import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
const MatrixSans = localFont({ src: "./fonts/MatrixSans-Regular.woff2",
  variable: "--font-matrix-sans", weight: "400", display: "swap", adjustFontFallback: false });
const MatrixSansVideo = localFont({ src: "./fonts/MatrixSansVideo-Regular.woff2",
  variable: "--font-matrix-video", weight: "400", display: "swap", adjustFontFallback: false });
export const metadata: Metadata = { title: "GitPulse | Repository observatory",
  description: "A clear view of repository activity. Explainable metrics, repeatable imports." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en" className={`${MatrixSans.variable} ${MatrixSansVideo.variable}`}><body>{children}</body></html>;
}
