import { fixturePayload } from "./fixtures";
import type { DemoPayload } from "./contract";

// Phase 1 : données fictives. La phase 2 branchera ici l'adaptateur S3.
export function getDemoPayload(): DemoPayload {
  return fixturePayload;
}
