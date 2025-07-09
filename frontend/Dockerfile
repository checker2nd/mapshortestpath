# frontend/Dockerfile

# 1) ビルド用ステージ
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# 2) 本番用ステージ：軽量なnginxで静的ファイルを配信
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html

# 必要ならカスタムnginx設定を追加
# COPY nginx.conf /etc/nginx/conf.d/default.conf
