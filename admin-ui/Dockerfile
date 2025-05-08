# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install only production dependencies
RUN npm install --omit=dev

# Copy the rest of the application code (including the pre-built CSS)
COPY . .

# Expose port 3000
EXPOSE 3000

# Command to run the application
CMD [ "npm", "start" ]