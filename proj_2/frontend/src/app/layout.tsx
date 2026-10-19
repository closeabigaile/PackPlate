import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PackPlate",
  description: "NC State dining, filtered for your whole group",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <SiteHeader />
        {children}
        <footer className="site-footer">
          <p>
            PackPlate is a student project, not run by NC State Dining. Menus
            come from NC State’s NetNutrition and hours from dining.ncsu.edu.
            If you have a serious allergy, check the label or ask dining staff
            before you eat.
          </p>
        </footer>
      </body>
    </html>
  );
}
