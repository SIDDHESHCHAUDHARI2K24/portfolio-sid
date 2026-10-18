import { defineRailway, github, image, postgres, preserve, project, service, volume } from "railway/iac";

// Watch paths (E04-W4): each service rebuilds only when its own code changes,
// so a frontend-only push never races a backend restart. Patterns are
// gitignore-style and evaluated from the repo root, even with rootDirectory.
const BACKEND_WATCH = ["/backend/**", "/Dockerfile"];

export default defineRailway(() => {
  const portfolioSid = github("SIDDHESHCHAUDHARI2K24/portfolio-sid", { checkSuites: true });

  const Postgres = postgres("Postgres", { region: "sfo" });
  const backendVolume = volume("backend-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "sfo", sizeMB: 50000 });
  const postgresVolume = volume("postgres-volume", { alerts: { usage: { "100": {}, "80": {}, "95": {} } }, allowOnlineResize: true, region: "sfo", sizeMB: 50000 });

  // pgbouncer is the only service holding the Postgres URL — everything else
  // reaches Postgres through pgbouncer:6432 (see docs/conventions.md §Connection pooling).
  const pgbouncer = service("pgbouncer", {
    source: image("edoburu/pgbouncer:1.22.1-p0"),
    replicas: { "sfo": 1 },
    env: {
      DATABASE_URL: Postgres.env.DATABASE_URL,
      ADMIN_USERS: preserve(),
      AUTH_TYPE: preserve(),
      DEFAULT_POOL_SIZE: preserve(),
      IGNORE_STARTUP_PARAMETERS: preserve(),
      LISTEN_ADDR: preserve(),
      LISTEN_PORT: preserve(),
      MAX_CLIENT_CONN: preserve(),
      POOL_MODE: preserve(),
      RESERVE_POOL_SIZE: preserve(),
      SERVER_RESET_QUERY: preserve(),
    },
  });

  const backend = service("backend", {
    source: portfolioSid,
    build: { buildEnvironment: "V3", builder: "DOCKERFILE", dockerfilePath: "/Dockerfile", watchPatterns: BACKEND_WATCH },
    healthcheck: "/api/v1/health",
    replicas: { "sfo": 1 },
    volumeMounts: { "/data": backendVolume },
    env: {
      // Composed references: password from the Postgres plugin, host from the
      // pgbouncer service — the only literal-free way to route through pgbouncer.
      DATABASE_URL: "postgresql+asyncpg://postgres:${{Postgres.POSTGRES_PASSWORD}}@${{pgbouncer.RAILWAY_PRIVATE_DOMAIN}}:6432/railway",
      ADMIN_EMAIL: preserve(),
      ADMIN_PASSWORD_HASH: preserve(),
      CF_ACCESS_ENABLED: preserve(),
      DATABASE_MAX_OVERFLOW: preserve(),
      DATABASE_POOL_SIZE: preserve(),
      ENVIRONMENT: preserve(),
      LOCAL_STORAGE_DIR: preserve(),
      MEDIA_BASE_URL: preserve(),
      NEXT_PUBLIC_BASE_URL: preserve(),
      PGBOUNCER_ENABLED: preserve(),
      RESEND_API_KEY: preserve(),
      RESEND_FROM: preserve(),
      REVALIDATION_SECRET: preserve(),
      SESSION_SECRET: preserve(),
      STORAGE_KIND: preserve(),
      TRUSTED_PROXY_CIDRS: preserve(),
    },
  });

  const cron = service("cron", {
    source: portfolioSid,
    build: { buildEnvironment: "V3", builder: "DOCKERFILE", dockerfilePath: "/Dockerfile", watchPatterns: BACKEND_WATCH },
    start: "python -m app.jobs.scheduler",
    replicas: { "sfo": 1 },
    deploy: { cronSchedule: "*/5 * * * *", restartPolicyType: "NEVER" },
    env: {
      DATABASE_URL: "postgresql+asyncpg://postgres:${{Postgres.POSTGRES_PASSWORD}}@${{pgbouncer.RAILWAY_PRIVATE_DOMAIN}}:6432/railway",
      ENVIRONMENT: preserve(),
      LOCAL_STORAGE_DIR: preserve(),
      MEDIA_BASE_URL: preserve(),
      NEXT_PUBLIC_BASE_URL: preserve(),
      PGBOUNCER_ENABLED: preserve(),
      REVALIDATION_SECRET: preserve(),
      STORAGE_KIND: preserve(),
    },
  });

  const frontend = service("frontend", {
    source: github("SIDDHESHCHAUDHARI2K24/portfolio-sid", { checkSuites: true, rootDirectory: "/frontend" }),
    build: { watchPatterns: ["/frontend/**"] },
    start: "npm run start",
    healthcheck: "/",
    replicas: { "sfo": 1 },
    domains: ["siddhesh-chaudhari.com"],
    env: {
      BACKEND_URL: "http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8080",
      NEXT_PUBLIC_BASE_URL: preserve(),
      NEXT_PUBLIC_INDEXABLE: preserve(),
      PUBLIC_API_PROXY: preserve(),
      REVALIDATION_SECRET: preserve(),
    },
  });

  const admin = service("admin", {
    source: github("SIDDHESHCHAUDHARI2K24/portfolio-sid", { checkSuites: true, rootDirectory: "admin" }),
    build: { buildEnvironment: "V3", builder: "DOCKERFILE", dockerfilePath: "admin/Dockerfile", watchPatterns: ["/admin/**"] },
    replicas: { "sfo": 1 },
    domains: ["admin.siddhesh-chaudhari.com"],
    env: {
      BACKEND_UPSTREAM: "http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8080",
    },
  });

  return project("portfolio-sid-v2", {
    resources: [cron, frontend, Postgres, admin, pgbouncer, backend, backendVolume, postgresVolume],
  });
});
