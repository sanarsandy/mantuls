# ======================================
# Build Stage
# ======================================
FROM node:22-alpine AS base

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# ======================================
# Development Stage
# ======================================
FROM base AS development
ENV NODE_ENV=development
CMD ["npm", "run", "dev", "--", "-o"]

# ======================================
# Builder Stage
# ======================================
FROM base AS builder
RUN npm run build

# ======================================
# Production Stage
# ======================================
FROM node:22-alpine AS production

WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -u 1001 -S nuxtjs -G nodejs

# Copy built output
COPY --from=builder --chown=nuxtjs:nodejs /app/.output ./

# Symlink for Nuxt chunks
RUN mkdir -p /app/server/chunks && ln -s /app/public /app/server/chunks/public

ENV NODE_ENV=production
ENV NITRO_HOST=0.0.0.0
ENV NITRO_PORT=3000
ENV NITRO_PRESET=node-server

# Switch to non-root user
USER nuxtjs

EXPOSE 3000

CMD ["node", "server/index.mjs"]
