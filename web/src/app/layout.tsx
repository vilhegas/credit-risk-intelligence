import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Credit Risk Intelligence | Análise de risco de crédito",
  description:
    "Projeto educacional de análise de risco de crédito: dados, modelagem e simulação de políticas com evidências e limitações explícitas.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <a className="skip-link" href="#conteudo">
          Pular para o conteúdo
        </a>
        {children}
      </body>
    </html>
  );
}
