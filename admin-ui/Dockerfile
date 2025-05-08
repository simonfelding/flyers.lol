# ---- Builder Stage ----
FROM node:22-alpine AS builder

WORKDIR /usr/src/app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm install

# Copy the rest of the application source code
COPY tsconfig.json ./
COPY src/ ./src/
COPY public/ ./public/
COPY views/ ./views/

RUN npm run build

# Prune devDependencies to prepare for copying to the final stage
# This creates a node_modules folder with only production dependencies
RUN npm prune --production

# ---- Final Stage ----
FROM node:22-alpine

WORKDIR /usr/src/app

# Set NODE_ENV to production
ENV NODE_ENV=production

COPY package.json ./
# Copy only production node_modules from the builder stage
COPY --from=builder /usr/src/app/node_modules ./node_modules

# Copy the compiled application from the builder stage
COPY --from=builder /usr/src/app/dist ./dist
COPY --from=builder /usr/src/app/public ./public
COPY --from=builder /usr/src/app/views ./views

ADD https://raw.githubusercontent.com/simonfelding/flyers.lol/refs/heads/main/openapi.yml /usr/src/app/openapi.yml
# Expose port 3000
EXPOSE 3000

# Command to run the compiled application
# This will directly run the compiled application
CMD [ "node", "dist/index.js" ]