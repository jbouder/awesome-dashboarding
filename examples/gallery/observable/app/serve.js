// A tiny static server for the built site in dist/. No dependencies.
import {createReadStream} from "node:fs";
import {stat} from "node:fs/promises";
import {createServer} from "node:http";
import {extname, join, normalize, resolve} from "node:path";

const root = resolve("dist");
const port = Number(process.env.PORT ?? 3000);
const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json",
  ".csv": "text/csv; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2"
};

async function find(pathname) {
  const path = normalize(join(root, decodeURIComponent(pathname)));
  if (!path.startsWith(root)) return null;
  // Framework links pages without the .html extension.
  for (const candidate of [path, `${path}.html`, join(path, "index.html")]) {
    const info = await stat(candidate).catch(() => null);
    if (info?.isFile()) return candidate;
  }
  return null;
}

createServer(async (req, res) => {
  const {pathname} = new URL(req.url, "http://localhost");
  const file = await find(pathname).catch(() => null);
  if (!file) {
    res.writeHead(404, {"content-type": "text/plain"}).end("Not found\n");
    return;
  }
  res.writeHead(200, {
    "content-type": types[extname(file)] ?? "application/octet-stream",
    // Hashed assets never change. Pages always revalidate.
    "cache-control": file.endsWith(".html") ? "no-cache" : "public, max-age=31536000, immutable"
  });
  createReadStream(file).pipe(res);
}).listen(port, () => console.log(`Serving ${root} on port ${port}`));
