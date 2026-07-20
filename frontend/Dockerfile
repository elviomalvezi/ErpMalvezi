# ── Etapa 1: Build Angular ───────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npx ng build --configuration=production

# ── Etapa 2: Servir com nginx ─────────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove config padrão
RUN rm /etc/nginx/conf.d/default.conf

# Copia arquivos buildados
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

# Copia config do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
