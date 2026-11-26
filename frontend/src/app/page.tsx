import { Suspense } from "react";
import { Demo } from "@/components/demo/Demo";

type HomeProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default function Home({ searchParams }: HomeProps) {
  return (
    <main className="demo">
      <header className="demo-header">
        <h1 className="demo-title">Cétolog · démo de matching</h1>
        <p className="demo-intro">
          Maquette filaire sur données fictives : ni bucket ni photo Miraceti.
        </p>
      </header>
      <Suspense fallback={<p className="demo-fallback">Chargement…</p>}>
        <Demo searchParams={searchParams} />
      </Suspense>
    </main>
  );
}
