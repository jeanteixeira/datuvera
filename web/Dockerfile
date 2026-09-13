FROM node:20-alpine AS deps
WORKDIR /usr/src/app

# Install small build tools needed by some native deps during install
RUN apk add --no-cache python3 make g++ libc6-compat

# Copy package manifests only and install dependencies (ci when possible)
COPY package.json package-lock.json ./
# Require an existing package-lock.json for reproducible builds
RUN if [ ! -f package-lock.json ]; then echo "package-lock.json missing; aborting build for reproducibility" && exit 1; fi
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /usr/src/app
# Copy node_modules from deps stage to speed up install
COPY --from=deps /usr/src/app/node_modules ./node_modules
# Copy all sources
COPY . .

# Build the Next.js app (will use installed deps)
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /usr/src/app
ENV NODE_ENV=production

# Copy only what is needed to run the app
COPY --from=builder /usr/src/app/.next ./.next
COPY --from=builder /usr/src/app/package.json ./package.json
COPY --from=builder /usr/src/app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]
