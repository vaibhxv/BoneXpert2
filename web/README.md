# BoneXpert 2.0 — Web UI

A React + Vite single-page app for loading a hand radiograph and viewing the
estimated skeletal age. Talks to the NestJS gateway at `/api` (same origin).

## Design

A "radiograph light-box × anatomical atlas" theme — deliberately not a generic
dashboard:

- **Palette:** film-black canvas, bone ivory, electric x-ray **phosphor** (lime),
  radiographic amber. No stock blues/purples.
- **Type:** `Fraunces` (editorial variable serif) for display, `Space Grotesk`
  for UI, `JetBrains Mono` for clinical readouts. Bundled via `@fontsource`
  (self-hosted, offline — no Google Fonts CDN).
- **Signature elements:** a self-drawing anatomical hand-skeleton SVG, film grain
  overlay, an animated scan-line during inference, and the returned crop
  bounding box drawn over the radiograph with a live confidence tag.

## Scripts

```bash
npm run dev       # Vite dev server on :5173 (proxies /api -> :3000)
npm run build     # type-check + production build to dist/
npm run preview   # preview the production build
```

In production the built `dist/` is served by the NestJS gateway, so you don't
run this app separately — see the root `README.md` and `make deploy`.

## Structure

```
src/
  components/   HandSkeleton, Uploader, ScanViewer, ResultConsole, SexToggle,
                HealthBadge, CountUp
  lib/api.ts    typed client for the NestJS /api/bone-age endpoints
  styles/       global.css (design tokens) + app.css (layout/components)
  App.tsx       upload → analyze → result state machine
```
