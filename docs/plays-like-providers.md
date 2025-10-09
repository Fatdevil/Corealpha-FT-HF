# Plays-like provider proxies

Two lightweight HTTP endpoints proxy Open-Meteo data so that "plays-like" experiences
can piggyback on a single, throttled integration point. Both endpoints share the same
behavioural guarantees:

- Responses are cached in-memory and on-disk to shield Open-Meteo and avoid cold-starts.
- Each payload advertises a strong `ETag` derived from the JSON body (excluding the
  `etag` property itself).
- Clients receive `Cache-Control: public` with a `max-age` that mirrors the backing TTL
  so that intermediaries can coalesce requests.
- Supplying `If-None-Match` yields a `304 Not Modified` as soon as the cached payload
  still applies.

## Elevation (`/providers/elevation`)

- **Quota impact**: elevation lookups are effectively free after the first hit because
  a 7-day TTL keeps both memory and file caches hot.
- **Response**: `{ "elevation_m": <float>, "ttl_s": 604800, "etag": <hash> }`
- **Data quality**: Open-Meteo interpolates across global elevation models. Expect
  ±20 m variance in mountainous terrain; the cache smooths repeated reads for nearby
  tiles.

## Wind (`/providers/wind`)

- **Quota impact**: cached for 15 minutes, keeping hourly polling well below Open-Meteo's
  generous free-tier limits.
- **Response**: `{ "speed_mps": <float>, "dir_from_deg": <float>, "ttl_s": 900,
  "etag": <hash>, "w_parallel": <float?>, "w_perp": <float?> }` where the optional
  components appear only if a `bearing` query parameter is supplied.
- **Data quality**: results rely on the `current`/hourly 10 m wind model. Gusts and
  microclimates are not captured. `w_parallel` reports head/tail wind (negative values
  mean headwind) relative to the supplied bearing and `w_perp` reports crosswind with
  a positive value denoting pressure from the right-hand side of travel.

## Operational notes

- Cache files live under `PROVIDERS_CACHE_DIR` if set, otherwise a system temporary
  directory. A warm cache means most lookups are served without external HTTP calls.
- HTTP failures or malformed responses bubble up as `502 Bad Gateway`; callers should
  implement retries with exponential backoff in the rare case of upstream outages.
- Because ETags embed the entire JSON payload, any schema evolution will naturally
  invalidate cached bodies and trigger a fresh fetch.
