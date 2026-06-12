import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "TaxBridge Brasil — Reforma Tributária sem sustos",
  description:
    "Simule, parametrize e acompanhe o impacto da transição CBS/IBS/IS (2026–2033) na sua empresa.",
};

const themeScript = `
try {
  const stored = localStorage.getItem('tb_theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (stored === 'dark' || (!stored && prefersDark)) document.documentElement.classList.add('dark');
} catch (e) {}
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="font-sans text-slate-900 antialiased dark:text-slate-100">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
