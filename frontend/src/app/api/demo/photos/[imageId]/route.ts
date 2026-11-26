import { photoLabel } from "@/demo/contract";
import { getDemoPayload } from "@/demo/get-demo";

function escapeXml(value: string): string {
  const escaped: Record<string, string> = {
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
  };
  return value.replace(/[<>&"']/g, (char) => escaped[char] ?? char);
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ imageId: string }> },
) {
  const { imageId } = await params;

  // Seuls les identifiants du contrat sont servis : pas d'accès arbitraire au bucket.
  const label = photoLabel(await getDemoPayload(), imageId);
  if (!label) {
    return new Response("Photo fictive inconnue", {
      status: 404,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }

  const title = escapeXml(label);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="260" viewBox="0 0 400 260"><title>${title}</title><rect x="0.5" y="0.5" width="399" height="259" fill="#fff" stroke="#000"/><text x="200" y="128" text-anchor="middle" font-family="monospace" font-size="16" fill="#000">${title}</text><text x="200" y="152" text-anchor="middle" font-family="monospace" font-size="12" fill="#000">photo fictive</text></svg>`;

  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
