import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "GIG.AI",
  description: "AI Freelance Command Centre",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-canvas text-text-primary font-inter">
        <AuthProvider>
          <Toaster 
            position="top-right" 
            toastOptions={{
              style: {
                borderRadius: '0px',
                background: '#111111',
                color: '#FFFFFF',
                border: '1px solid #2A2A2A',
                fontSize: '13px',
                fontFamily: 'Inter, sans-serif'
              }
            }}
          />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
