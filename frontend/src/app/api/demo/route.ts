import { getDemoPayload } from "@/demo/get-demo";

export function GET() {
  return Response.json(getDemoPayload());
}
