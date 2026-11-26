import type { Metadata } from "next";
import { Bricolage_Grotesque, Geist, Geist_Mono } from "next/font/google";
import { SiteHeader } from "@/components/SiteHeader";
import { ProfileSync } from "@/lib/accountProfile";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Headings and the logo: a display face with more character than the body text.
const display = Bricolage_Grotesque({
  variable: "--font-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PackPlate",
  description: "NC State dining, filtered for your whole group",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${display.variable}`}
    >
      <body>
        <SiteHeader />
        <ProfileSync />
        {children}
        <footer className="site-footer">
          <div className="site-footer-inner">
            <p className="footer-brand">
              Pack<span>Plate</span>
            </p>
            <p>
              PackPlate is a student project, not run by NC State Dining. Menus
              come from NC State’s NetNutrition and hours from dining.ncsu.edu.
              If you have a serious allergy, check the label or ask dining staff
              before you eat.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
