export const config = {
  project: {
    name: "openleads-ai",
  },
  resources: [
    {
      type: "postgres",
      name: "openleads-db",
    },
    {
      type: "redis",
      name: "openleads-redis",
    },
    {
      type: "docker",
      name: "backend",
      dockerfilePath: "./backend/Dockerfile",
      env: {
        SECRET_KEY: "super-secret-key-change-in-production",
        FRONTEND_URL: "",
        BACKEND_URL: "",
      },
    },
    {
      type: "docker",
      name: "celery-worker",
      dockerfilePath: "./backend/Dockerfile",
      command: "celery -A app.core.celery_app worker --loglevel=info",
    },
    {
      type: "docker",
      name: "frontend",
      dockerfilePath: "./frontend/Dockerfile",
      env: {
        NEXT_PUBLIC_API_URL: "",
      },
    },
  ],
};
