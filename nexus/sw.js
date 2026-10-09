const CACHE = "zettacore-nexus-shell-v1";
const CORE = ["/", "/manifest.webmanifest", "/icons/nexus-192.svg", "/icons/nexus-512.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(CORE)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith(
    fetch(request).then((response) => {
      if (response.ok && request.mode === "navigate") {
        const copy = response.clone();
        caches.open(CACHE).then((cache) => cache.put("/", copy));
      }
      return response;
    }).catch(async () => {
      const cached = await caches.match(request);
      return cached || (request.mode === "navigate" ? caches.match("/") : Response.error());
    })
  );
});