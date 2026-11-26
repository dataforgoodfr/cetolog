import { getDemoPayload } from "@/demo/get-demo";

export async function GET() {
  const payload = await getDemoPayload();
  return Response.json(payload, { headers: { "Cache-Control": "no-store" } });
}
