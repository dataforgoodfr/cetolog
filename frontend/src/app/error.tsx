"use client";

export default function Error({
  reset,
}: {
  error: unknown;
  reset: () => void;
}) {
  return (
    <main className="demo">
      <h1>Erreur</h1>
      <p className="demo-empty">
        La démo n’a pas pu charger ses données fictives.
      </p>
      <button type="button" className="demo-button" onClick={reset}>
        Réessayer
      </button>
    </main>
  );
}
