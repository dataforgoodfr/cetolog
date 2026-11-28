import { GetObjectCommand, HeadObjectCommand } from "@aws-sdk/client-s3";

import { findPhoto, getS3Client } from "@/lib/catalog/photo-gateway";
import { resolveS3KeyCandidates } from "@/lib/catalog/s3-key";
import type { CatalogErrorBody } from "@/types/catalog";

export async function GET(
  _request: Request,
  context: { params: Promise<{ imageId: string }> },
): Promise<Response> {
  const { imageId } = await context.params;

  try {
    const photo = await findPhoto(imageId);
    if (!photo) return new Response(null, { status: 404 });

    const candidates = resolveS3KeyCandidates(photo);
    if (!candidates) return new Response(null, { status: 404 });

    const bucket = process.env.S3_BUCKET;
    if (!bucket) throw new Error("S3_BUCKET manquant");

    const client = getS3Client();
    let key: string | undefined;
    for (const candidate of candidates) {
      try {
        await client.send(
          new HeadObjectCommand({ Bucket: bucket, Key: candidate }),
        );
        key = candidate;
        break;
      } catch {
        // Candidat suivant : la livraison n'a pas unifié les noms de fichiers.
      }
    }
    if (!key) return new Response(null, { status: 503 });

    const object = await client.send(
      new GetObjectCommand({ Bucket: bucket, Key: key }),
    );
    const bytes = await object.Body?.transformToByteArray();
    if (!bytes) return new Response(null, { status: 503 });
    const buffer = new ArrayBuffer(bytes.byteLength);
    new Uint8Array(buffer).set(bytes);

    return new Response(buffer, {
      headers: {
        "Content-Type": object.ContentType ?? "image/jpeg",
        "Cache-Control": "private, no-store",
      },
    });
  } catch (error) {
    console.error("catalog: image indisponible", error);
    const body: CatalogErrorBody = {
      code: "UPSTREAM_UNAVAILABLE",
      message: "Image temporairement indisponible.",
    };
    return Response.json(body, { status: 503 });
  }
}
