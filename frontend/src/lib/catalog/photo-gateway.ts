import "server-only";

import { S3Client } from "@aws-sdk/client-s3";

import { getCatalogPool } from "./postgres-gateway";

export type PhotoRecord = {
  id: number;
  delivery: string;
  original_filename: string;
};

export async function findPhoto(id: string): Promise<PhotoRecord | null> {
  if (!/^\d+$/.test(id)) return null;

  const { rows } = await getCatalogPool().query<PhotoRecord>(
    `select id, delivery, original_filename from photos where id = $1`,
    [id],
  );
  return rows[0] ?? null;
}

let client: S3Client | undefined;

export function getS3Client(): S3Client {
  if (
    !process.env.S3_ENDPOINT_URL ||
    !process.env.S3_REGION ||
    !process.env.S3_BUCKET ||
    !process.env.AWS_ACCESS_KEY_ID ||
    !process.env.AWS_SECRET_ACCESS_KEY
  ) {
    throw new Error("Variables S3 manquantes pour servir une photo");
  }
  client ??= new S3Client({
    endpoint: process.env.S3_ENDPOINT_URL,
    region: process.env.S3_REGION,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
    },
  });
  return client;
}
