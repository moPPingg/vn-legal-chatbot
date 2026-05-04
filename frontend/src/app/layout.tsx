import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LegalAI",
  description: "Trợ lý pháp luật Việt Nam",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="bg-white m-0 p-0 overflow-hidden">
        {children}
      </body>
    </html>
  );
}
