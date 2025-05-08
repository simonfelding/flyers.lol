# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Add the openapi schema to the container - but note that this is only there as a backup in case github is unavailable.
ADD https://raw.githubusercontent.com/simonfelding/flyers.lol/refs/heads/main/openapi.yml /usr/src/app/openapi.yml

# Install only production dependencies
RUN npm install --omit=dev

# Copy the rest of the application code (including the pre-built CSS)
COPY . .

# Expose port 3000
EXPOSE 3000

# Command to run the application
CMD [ "npm", "start" ]