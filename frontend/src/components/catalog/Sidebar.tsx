const NAV_ITEMS = ["Observations", "Catalogue", "Historique", "Qualité"];

export function Sidebar() {
  return (
    <aside className="catalog-sidebar">
      <p className="catalog-logo">Cetolog</p>
      <button type="button" className="catalog-matching-cta">
        + Lancer un matching
      </button>
      <nav aria-label="Navigation principale">
        <ul className="catalog-nav">
          {NAV_ITEMS.map((label) => (
            <li key={label}>
              {label === "Catalogue" ? (
                <a href="/catalogue" aria-current="page">
                  {label}
                </a>
              ) : (
                <span title="À venir">{label}</span>
              )}
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
