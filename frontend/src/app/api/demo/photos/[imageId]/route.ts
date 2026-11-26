import { photoLabel } from "@/demo/contract";
import { getDemoPayload, resolveImageKey } from "@/demo/get-demo";
import { readObject } from "@/demo/s3";

const CONTENT_TYPES: Record<string, string> = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  webp: "image/webp",
};

function contentType(key: string): string {
  const extension = key.split(".").at(-1)?.toLowerCase() ?? "";
  return CONTENT_TYPES[extension] ?? "application/octet-stream";
}

function text(message: string, status: number): Response {
  return new Response(message, {
    status,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ imageId: string }> },
) {
  const { imageId } = await params;
  // Le contrat est la source de vérité : aucun identifiant hors allowlist n'est résolu.
  const payload = await getDemoPayload();
  if (!photoLabel(payload, imageId)) return text("Photo inconnue", 404);
  const key = resolveImageKey(imageId);
  if (!key) return text("Photo inconnue", 404);

  try {
    const bytes = await readObject(key);
    // Le SDK renvoie un Uint8Array valide comme BodyInit à l'exécution.
    return new Response(bytes as unknown as BodyInit, {
      headers: {
        "Content-Type": contentType(key),
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch {
    // Ne pas renvoyer la clé S3 : elle peut contenir un nom de photographe.
    return text("Photo indisponible", 503);
  }
}
