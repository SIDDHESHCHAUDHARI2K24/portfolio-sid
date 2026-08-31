# Admin SPA — isolated service for admin.siddhesh-chaudhari.com
# Build context = admin/ folder (when deployed via `railway up` from admin/ or
# Railway Root Directory /admin). COPY paths are relative to admin/.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . ./
RUN npm run build

FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Railway injects PORT; template PORT and the runtime DNS resolver so nginx
# re-resolves backend.railway.internal at request time
CMD sh -c "RESOLVER=\$(sed -n 's/^nameserver[[:space:]]*\(.*:.*\)$/[\1]/p; s/^nameserver[[:space:]]*//p' /etc/resolv.conf | head -1) envsubst '\$PORT \$RESOLVER' < /etc/nginx/conf.d/default.conf > /tmp/default.conf && mv /tmp/default.conf /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
