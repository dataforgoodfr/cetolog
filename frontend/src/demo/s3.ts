import {
  GetObjectCommand,
  ListObjectsV2Command,
  S3Client,
} from "@aws-sdk/client-s3";

let client: S3Client | undefined;

function getClient(): S3Client {
  if (client) return client;

  const required = [
    "S3_ENDPOINT_URL",
    "S3_REGION",
    "S3_BUCKET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
  ];
  const missing = required.filter((name) => !process.env[name]);
  // Ne jamais inclure les valeurs : le message peut s'afficher dans la page.
  if (missing.length > 0) {
    throw new Error(`Variables S3 manquantes : ${missing.join(", ")}`);
  }

  client = new S3Client({
    endpoint: process.env.S3_ENDPOINT_URL,
    region: process.env.S3_REGION,
    // Cellar refuse les sommes de contrôle par défaut du SDK, comme dans pipeline/storage.py.
    requestChecksumCalculation: "WHEN_REQUIRED",
    responseChecksumValidation: "WHEN_REQUIRED",
  });
  return client;
}

function bucket(): string {
  return process.env.S3_BUCKET as string;
}

export async function readObject(key: string): Promise<Uint8Array> {
  const response = await getClient().send(
    new GetObjectCommand({ Bucket: bucket(), Key: key }),
  );
  if (!response.Body) throw new Error("Objet S3 vide");
  return response.Body.transformToByteArray();
}

export async function readText(key: string): Promise<string> {
  return new TextDecoder().decode(await readObject(key));
}

export async function listObjects(prefix: string): Promise<string[]> {
  const keys: string[] = [];
  let continuationToken: string | undefined;
  do {
    const response = await getClient().send(
      new ListObjectsV2Command({
        Bucket: bucket(),
        Prefix: prefix,
        ContinuationToken: continuationToken,
      }),
    );
    for (const item of response.Contents ?? []) {
      if (item.Key && !item.Key.endsWith("/")) keys.push(item.Key);
    }
    continuationToken = response.NextContinuationToken;
  } while (continuationToken);
  return keys;
}
