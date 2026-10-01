# LeafyAI Frontend

The LeafyAI frontend is a React + TypeScript application built with Vite.

It is the operator interface for farm selection, monitoring, sensor/camera configuration, growth management, AI recommendations and powerboard controls.

## Stack

```text
React 19
TypeScript
Vite 8
Tailwind CSS
React Router
Vitest
```

## Development with Docker

The normal project workflow starts the frontend from the repository root:

```powershell
docker compose up --build
```

Open:

```text
http://localhost:5173
```

`docker-compose.yml` provides:

```text
VITE_BACKEND_BASEURL
```

with a default of:

```text
http://127.0.0.1:8000
```

## Local frontend-only development

From `frontend/`:

```powershell
npm install
npm run dev
```

The backend still needs to be reachable at the configured `VITE_BACKEND_BASEURL`.

## Main pages

Authenticated application routes currently include:

```text
/farm-overview
/ai-agent
/growth-harvesting
/history
/settings
```

Authentication is handled through the login/register pages and JWT tokens returned by the Django backend.

## Data flow

The frontend keeps API access in:

```text
src/util/api-service-layer.ts
src/util/constants.ts
```

The main shared state providers are:

```text
UserProvider
FarmOverviewProvider
AiAgentProvider
GrowthHarvestProvider
```

`FarmOverviewProvider` owns the selected farm and refreshes farm state, dashboard data, powerboard status and sensor-ingestion timing.

`AiAgentProvider` loads farm-specific AI settings and recommendation runs and polls recent recommendation state while the application is active.

`GrowthHarvestProvider` keeps growing-area and batch data scoped to the currently selected farm.

## Farm creation

The frontend sends the new farm record to:

```text
POST /api/farms/
```

The frontend does not manually create the standard controller/sensors/levels. That provisioning is handled by the backend transaction.

After creation, operators can configure sensor ingestion and cameras for the selected farm.

## Powerboard UI

The frontend uses the backend powerboard endpoints:

```text
GET  /api/devices/
POST /api/devices/{device_id}/state/
```

The logical device IDs in `src/util/constants.ts` must remain aligned with `backend/powerboard_control/config.py`.

## Camera and sensor UI

Farm-scoped URLs are built in `src/util/constants.ts`.

The frontend does not contact physical sensor or RTSP addresses directly. Browser requests go to Django; the backend owns hardware communication.

## AI UI

The AI page supports:

- per-farm provider/model configuration
- provider connection testing
- manual recommendation generation
- latest/recent recommendation display
- scheduled recommendation configuration
- display of VLM/LLM mode, fallback information, safety state and action results

AI secrets are submitted to the backend and are not intended to be persisted in browser source files.

## Build and tests

From `frontend/`:

```powershell
npm test -- --run
npm run build
npm run lint
```

With Docker:

```powershell
docker compose exec frontend npm test -- --run
docker compose exec frontend npm run build
docker compose exec frontend npm run lint
```

## Source layout

```text
src/
├── components/       Reusable UI components
├── pages/            Route-level pages
├── providers/        Shared application state/providers
├── test/             Frontend tests
├── util/             API clients, route builders and helpers
├── App.tsx
└── main.tsx
```

## Maintenance notes

- Keep backend URLs centralized in `src/util/constants.ts`.
- Keep hardware communication on the backend; the frontend should use REST APIs only.
- Keep farm-scoped state synchronized when the selected farm changes.
- Update TypeScript API types when backend response contracts change.
- Run both `npm run build` and `npm run lint` before handover/release.
