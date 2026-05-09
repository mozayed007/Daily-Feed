# Build stage
FROM oven-sh/bun:1 AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN bun install

COPY . .
RUN bun run build

# Serve with nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
