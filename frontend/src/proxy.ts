import { createHash, timingSafeEqual } from "node:crypto";
import { NextResponse, type NextRequest } from "next/server";

function equals(a: string, b: string): boolean {
  // Comparaison à temps constant : l'auth protège des photos privées.
  const left = createHash("sha256").update(a).digest();
  const right = createHash("sha256").update(b).digest();
  return timingSafeEqual(left, right);
}

function authorized(header: string | null): boolean {
  // Comme Gradio : sans DEMO_PASSWORD, la démo reste ouverte.
  const password = process.env.DEMO_PASSWORD;
  if (!password) return true;

  const match = header?.match(/^Basic\s+(\S+)$/i);
  if (!match) return false;

  const credentials = Buffer.from(match[1], "base64").toString("utf8");
  const separator = credentials.indexOf(":");
  if (separator < 0) return false;

  return (
    equals(
      credentials.slice(0, separator),
      process.env.DEMO_USER ?? "miraceti",
    ) && equals(credentials.slice(separator + 1), password)
  );
}

export function proxy(request: NextRequest) {
  if (!authorized(request.headers.get("authorization"))) {
    return new NextResponse("Authentification requise", {
      status: 401,
      headers: {
        "WWW-Authenticate": 'Basic realm="Cetolog demo", charset="UTF-8"',
        "Cache-Control": "no-store",
      },
    });
  }

  const response = NextResponse.next();
  if (process.env.DEMO_PASSWORD) {
    response.headers.set("Cache-Control", "no-store");
  }
  return response;
}

export const config = {
  matcher: ["/", "/api/:path*"],
};
