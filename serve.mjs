// Serves dist/ for docs.ashikanw.com (behind the Cloudflare Tunnel). No dependencies: node serve.mjs
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = join(fileURLToPath(new URL(".", import.meta.url)), "dist");
const PORT = Number(process.env.PORT || 3400);
const HOST = process.env.HOST || "127.0.0.1";
const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".png": "image/png", ".svg": "image/svg+xml", ".xml": "application/xml", ".txt": "text/plain; charset=utf-8",
};
const SECURITY = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Frame-Options": "DENY",
};

async function file(path) {
  try {
    const info = await stat(path);
    return info.isDirectory() ? file(join(path, "index.html")) : { body: await readFile(path), path };
  } catch {
    return null;
  }
}

createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405, { Allow: "GET, HEAD", ...SECURITY }).end();
    return;
  }
  let pathname;
  try {
    pathname = decodeURIComponent(url.pathname);
  } catch {
    pathname = "/";
  }
  const target = normalize(join(DIST, pathname));
  let found = target === DIST || target.startsWith(DIST + sep) ? await file(target) : null;
  // /api のような末尾の / が無い URL は、/api/ に寄せる（ページの中の相対リンクがずれないように）
  if (found && found.path.endsWith("index.html") && !pathname.endsWith("/")) {
    res.writeHead(301, { Location: pathname + "/" + url.search, ...SECURITY }).end();
    return;
  }
  let status = 200;
  if (!found) {
    status = 404;
    found = await file(join(DIST, "404.html"));
  }
  const type = TYPES[extname(found.path)] || "application/octet-stream";
  const cache = type.startsWith("text/html") ? "no-cache" : "public, max-age=3600";
  res.writeHead(status, { "Content-Type": type, "Cache-Control": cache, ...SECURITY });
  res.end(req.method === "HEAD" ? undefined : found.body);
}).listen(PORT, HOST, () => console.log(`docs on http://${HOST}:${PORT}`));
