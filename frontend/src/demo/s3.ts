import {
  GetObjectCommand,
  ListObjectsV2Command,
  S3Client,
} from "@aws-sdk/client-s3";

type Configuration = {
  endpoint: string;
  region: string;
  bucket: string;
  accessKeyId: string;
  secretAccessKey: string;
};

let client: S3Client | undefined;

function first(...names: string[]): string | undefined {
  return names.map((name) => process.env[name]).find(Boolean);
}

function configuration(): Configuration {
  // Clever Cloud injecte ces noms quand l'add-on Cellar est lié à l'app.
  const cellarHost = process.env.CELLAR_ADDON_HOST;
  const values = {
    endpoint:
      first("S3_ENDPOINT_URL") ??
      (cellarHost ? `https://${cellarHost}` : undefined),
    region: first("S3_REGION") ?? (cellarHost ? "us-east-1" : undefined),
    bucket: first("S3_BUCKET"),
    accessKeyId: first("AWS_ACCESS_KEY_ID", "CELLAR_ADDON_KEY_ID"),
    secretAccessKey: first("AWS_SECRET_ACCESS_KEY", "CELLAR_ADDON_KEY_SECRET"),
  };
  const labels = {
    endpoint: "S3_ENDPOINT_URL ou CELLAR_ADDON_HOST",
    region: "S3_REGION ou CELLAR_ADDON_HOST",
    bucket: "S3_BUCKET",
    accessKeyId: "AWS_ACCESS_KEY_ID ou CELLAR_ADDON_KEY_ID",
    secretAccessKey: "AWS_SECRET_ACCESS_KEY ou CELLAR_ADDON_KEY_SECRET",
  };
  const missing = (Object.keys(values) as (keyof Configuration)[])
    .filter((name) => !values[name])
    .map((name) => labels[name]);
  // Ne jamais inclure les valeurs : le message peut s'afficher dans la page.
  if (missing.length > 0) {
    throw new Error(`Variables S3 manquantes : ${missing.join(", ")}`);
  }

  return values as Configuration;
}

function getClient(): S3Client {
  if (client) return client;
  const config = configuration();
  client = new S3Client({
    endpoint: config.endpoint,
    region: config.region,
    credentials: {
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
    },
    // Cellar refuse les sommes de contrôle par défaut du SDK, comme dans pipeline/storage.py.
    requestChecksumCalculation: "WHEN_REQUIRED",
    responseChecksumValidation: "WHEN_REQUIRED",
  });
  return client;
}

export async function readObject(key: string): Promise<Uint8Array> {
  const response = await getClient().send(
    new GetObjectCommand({ Bucket: configuration().bucket, Key: key }),
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
        Bucket: configuration().bucket,
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
