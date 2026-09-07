# Frontend container image for VoiceShield.
# Multi-stage: build the static site with Node, then serve it with nginx.

# --- Build stage ---
FROM node:22-alpine AS build
WORKDIR /app

# Install deps first for better layer caching.
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Serve stage ---
FROM nginx:alpine
# SPA routing config (falls back to index.html).
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
