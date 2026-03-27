import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MedDiag Auth Web",
  description: "Login y sesiones con Supabase para MedDiag",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
