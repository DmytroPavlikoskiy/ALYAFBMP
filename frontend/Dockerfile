# node:20-alpine — lightweight, multi-arch (amd64 + arm64)
FROM node:20-alpine

WORKDIR /app

# ── Dependency layer (cached unless package*.json changes) ─────────────────
# `npm ci` installs the exact versions pinned in package-lock.json and is
# faster and more reproducible than `npm install` in CI/container builds.
COPY package*.json ./
RUN npm ci

# ── Application source ─────────────────────────────────────────────────────
# In development the whole directory is bind-mounted by docker-compose
# (overriding this COPY), but we still copy here so the image is self-
# contained and can be used without a volume (e.g. staging).
COPY . .

# Vite dev-server port
EXPOSE 5173

# --host binds Vite to 0.0.0.0 so it is reachable outside the container.
# Hot Module Replacement (HMR) works because docker-compose bind-mounts
# ./frontend into /app, and Vite watches the mounted files.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
