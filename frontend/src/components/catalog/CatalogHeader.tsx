export function CatalogHeader() {
  return (
    <header className="catalog-header">
      <div>
        <h1>Catalogue des individus</h1>
        <p>Tous les individus connus, avec leur photo de référence.</p>
      </div>
      <button type="button" className="catalog-import">
        Importer catalogue existant
      </button>
    </header>
  );
}
