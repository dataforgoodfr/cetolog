import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cétolog · démo de matching",
  description:
    "Portage option A de la démo Gradio, avec les propositions du pipeline.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
