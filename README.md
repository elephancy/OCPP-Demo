# ocpp-backend-demo

`ocpp-backend-demo` is a backend lifecycle demo for EV charging operations.
It focuses on the engineering judgment behind reliable OCPP ingestion, async processing, operational observability, and a product-quality dashboard rather than on billing, roaming, or a full charging platform.

## Scope

- Backend lifecycle demo, not a complete charging platform
- Multi-site fleet management
- OCPP 1.6 over WebSocket
- Python backend with FastAPI
- PostgreSQL as the source of truth
- SQLAlchemy and Alembic for persistence
- Redis for limited cache and worker-heartbeat use
- Durable outbox processing scaffolding
- Separate frontend and simulator containers
- Caddy reverse proxy
- JWT auth with `admin` and `operator` roles
- JSON logs and optional OpenTelemetry export using centrally managed Ops policy
- Per-station bearer-token authentication for OCPP WebSocket connections

## Repository Layout

- `backend/` - FastAPI app, domain logic, migrations, and tests
- `frontend/` - Next.js operations UI
- `simulator/` - Python simulator process
- `caddy/` - reverse proxy config
- `deploy/` - server-only environment templates

## Local Setup

1. Copy the local example environment: `cp .env.example .env`.
2. Start the stack:
   - `make up`
3. Open the demo through Caddy:
   - `http://localhost:8080`

The development stack runs without a telemetry collector by default. To test
tracing, obtain the reviewed collector configuration from the private Ops
repository (`config/telemetry/ocpp-collector.yaml`), set
`OPS_OTEL_COLLECTOR_CONFIG` to its absolute local path and
`OTEL_EXPORTER_OTLP_ENDPOINT` to the collector's OTLP HTTP endpoint, then run
`docker compose -f docker-compose.yml -f docker-compose.telemetry.yml up --build`.
The endpoint must be reachable from the backend container. Logging verbosity can
be selected with the standard `LOG_LEVEL` environment variable; an unconfigured
local run uses Python's WARNING threshold.

## Useful Commands

- `make up` - start the full Compose stack
- `make down` - stop the stack
- `make reset-demo` - reset Compose volumes, rebuild, start, and smoke-check a clean rehearsal state
- `make logs` - follow service logs
- `make test-backend` - run backend tests
- `make test-backend-postgres` - run repository locking tests against PostgreSQL
- `make test-frontend` - run frontend tests
- `make test-simulator` - run simulator tests
- `make test-simulator-integration` - run the simulator WebSocket integration test against the backend container
- `make smoke` - run the Compose smoke check

## Demo Flow

1. Log in as an operator or admin.
2. Review the overview dashboard for fleet health and backlog signals.
3. Inspect a site, then drill into a station and connector.
4. Run a simulator scenario such as a happy-path session, duplicate meter value, invalid partner signature, or duplicate partner event.
5. Observe raw OCPP messages, outbox processing, and webhook status.
6. As an admin, retry or acknowledge failed work and audit the action trail.

## Operations Notes

- Production runtime values are held by the private deployment controller. They are never committed or copied into repository-level GitHub secrets.
- Ops owns production log levels, telemetry endpoints, and the collector configuration. The controller mounts that configuration and injects its settings; this repository retains semantic application events and spans.
- Local demo data is controlled by `SEED_DEMO_DATA=true` in `.env`. It creates sample sites, stations, messages, and demo accounts for development only.
- The controller-managed production environment must keep `SEED_DEMO_DATA=false`.
- Creating the first production admin is an attended runtime operation: provide the bootstrap values through the controller, verify the account, and clear them immediately afterward.
- Do not use demo seeded accounts as a production bootstrap path.
- Rotate `PARTNER_WEBHOOK_SECRET` through a reviewed controller-managed runtime update; the UI shows this as a manual operator flow rather than an automated secret-manager integration.
- Configure `OCPP_STATION_TOKENS` as a JSON object mapping station external IDs to unique random tokens of at least 32 characters. The backend stores only SHA-256 token hashes.
- Chargers connect to `/ocpp/{station-id}` with `Authorization: Bearer <station-token>`. Admins can rotate a station token from the Admin view; update the charger and simulator environment with the same new token before reconnecting.
- Simulator state, scenario, and run endpoints require a currently active admin or operator bearer token.
- The database is the durable source of truth.
- Redis is used for short-lived station snapshots and worker heartbeat state. Most dashboard reads still query PostgreSQL directly.
- Worker processing is idempotent and outbox-backed. The current handlers mark OCPP messages and partner events processed; downstream webhook fanout, command dispatch, and projection consumers are not implemented.
- The controls named as simulated start/stop actions write audit events only. They do not call the simulator or send OCPP `RemoteStartTransaction` or `RemoteStopTransaction` commands.
- `StartTransaction` follows OCPP 1.6 ownership: the charger sends the request without a transaction ID, the central system returns one, and later `MeterValues` and `StopTransaction` requests reuse it.
- Detailed application spans go to the Ops-configured collector when an exporter endpoint is supplied. Local runs without one do not start an exporter.
- Demo JWTs are intentionally short-lived operational tokens, not refresh-token sessions. Expired tokens are cleared by the UI and require logging in again.
- Repository tests that need PostgreSQL use a disposable database URL through `OCPP_POSTGRES_TEST_URL`; do not point that variable at a database you want to keep.

## Troubleshooting

- If the stack fails to boot, check `docker compose logs -f`.
- If the UI cannot reach the API, confirm Caddy is listening on port `8080`.
- If OCPP traffic is not flowing, confirm the backend WebSocket endpoint, station ID, and matching entry in `OCPP_STATION_TOKENS`.
- If the database schema is missing, run the Alembic migration command in the backend container.

## Deployment

The private controller discovers reviewed `main` commits after the required `ci-deploy` workflow succeeds. It independently verifies the repository, branch, exact commit, and CI attempt before publishing immutable images and deploying them.

The private controller owns the release configuration, runtime configuration, routing, deployment policy, receipts, and rollback state. This repository keeps the backend, frontend, and simulator Dockerfiles and application CI, without a production caller or duplicate release manifest. No host login, private key, address, or filesystem path belongs in this repository or its GitHub configuration.

[`docker-compose.prod.yml`](docker-compose.prod.yml), [`deploy/.env.example`](deploy/.env.example), and [`deploy/Caddyfile.prod`](deploy/Caddyfile.prod) remain application-level runtime specifications. They are not direct production deployment instructions. Changes to the Dockerfiles or runtime specifications require production review.
