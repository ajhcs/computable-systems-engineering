import { DurableObject } from "cloudflare:workers";

interface Env {
  RUNTIME: DurableObjectNamespace<EngineeringRuntime>;
  REQUEST_LIMIT: RateLimit;
  ASSETS: Fetcher;
}

const MAX_BODY = 1_500_000;
const INACTIVITY_MS = 60_000;

export class EngineeringRuntime extends DurableObject<Env> {
  private starting?: Promise<void>;

  private async ready(): Promise<void> {
    const container = this.ctx.container!;
    if (!container.running) {
      container.start({ image: container.images.base, instance: "standard-1", enableInternet: false });
    }
    await container.setInactivityTimeout(INACTIVITY_MS);
    for (let attempt = 0; attempt < 60; attempt++) {
      try {
        const response = await container.getTcpPort(8080).fetch("http://container/health", {
          signal: AbortSignal.timeout(500),
        });
        await response.body?.cancel();
        if (response.ok) return;
      } catch { /* Startup readiness is retried within a bounded window. */ }
      await scheduler.wait(200);
    }
    throw new Error("Runtime readiness timeout");
  }

  async fetch(request: Request): Promise<Response> {
    this.starting ??= this.ready().finally(() => { this.starting = undefined; });
    await this.starting;
    const url = new URL(request.url);
    url.protocol = "http:";
    url.host = "container";
    const forwarded = new Request(url, request);
    // Client metadata and credentials are not needed by this anonymous calculator.
    for (const header of ["authorization", "cookie", "cf-connecting-ip", "x-forwarded-for", "forwarded", "host"]) {
      forwarded.headers.delete(header);
    }
    return this.ctx.container!.getTcpPort(8080).fetch(forwarded);
  }
}

function response(message: string, status: number): Response {
  return Response.json({ error: message }, { status, headers: { "Cache-Control": "no-store" } });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.hostname !== "cse.open-informatics.org") return response("Unknown host", 404);
    if (url.pathname !== "/mcp" && url.pathname !== "/health") {
      if (!["GET", "HEAD"].includes(request.method)) return response("Method not allowed", 405);
      return env.ASSETS.fetch(request);
    }
    if (url.pathname === "/health" && request.method !== "GET") return response("Method not allowed", 405);
    if (url.pathname === "/mcp" && request.method !== "POST") return response("Use stateless MCP POST requests", 405);
    const origin = request.headers.get("Origin");
    if (origin && !["https://chatgpt.com", "https://cse.open-informatics.org"].includes(origin)) {
      return response("Origin not allowed", 403);
    }
    const key = request.headers.get("CF-Connecting-IP") || "unknown";
    if (!(await env.REQUEST_LIMIT.limit({ key })).success) return response("Request limit reached", 429);
    if (request.headers.has("Content-Length") && Number(request.headers.get("Content-Length")) > MAX_BODY) {
      return response("Request too large", 413);
    }
    // Bound chunked bodies too; do not buffer arbitrary client input.
    const chunks: Uint8Array[] = [];
    let bytes = 0;
    if (request.body) {
      const reader = request.body.getReader();
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        bytes += value.byteLength;
        if (bytes > MAX_BODY) {
          await reader.cancel();
          return response("Request too large", 413);
        }
        chunks.push(value);
      }
    }
    const body = new Uint8Array(bytes);
    let offset = 0;
    for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
    const forwarded = new Request(request.url, {
      method: request.method, headers: request.headers, body: request.method === "GET" ? undefined : body,
    });
    try {
      // One shared stateless instance bounds active compute. No project/account store.
      const upstream = await env.RUNTIME.getByName("runtime-v1").fetch(forwarded);
      const output = new Response(upstream.body, upstream);
      output.headers.set("Cache-Control", "no-store");
      output.headers.set("X-Content-Type-Options", "nosniff");
      return output;
    } catch {
      return response("Engineering runtime unavailable; no check was completed", 503);
    }
  },
} satisfies ExportedHandler<Env>;
