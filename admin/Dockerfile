# Admin SPA — standalone service for admin.siddhesh-chaudhari.com
# Build context = repo root (Railway default). Dockerfile lives at admin/Dockerfile,
# so COPY paths are prefixed with admin/. To isolate, set Railway Source Root
# Directory = /admin and change these to COPY package.json ... (approach A).
FROM node:20-alpine AS build
WORKDIR /app
COPY admin/package.json admin/package-lock.json ./
RUN npm ci
COPY admin/ ./
RUN npm run build

FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY admin/nginx.conf /etc/nginx/conf.d/default.conf
# Railway injects PORT; run nginx after templating PORT
CMD sh -c "envsubst '\$PORT' < /etc/nginx/conf.d/default.conf > /tmp/default.conf && mv /tmp/default.conf /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
