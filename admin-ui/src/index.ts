import fastify, { FastifyInstance } from 'fastify';
import path from 'path';
import fastifyMultipart from '@fastify/multipart';
import fastifyView from '@fastify/view';
import fastifyFormbody from '@fastify/formbody';
import fastifyStatic from '@fastify/static';
import ejs from 'ejs';

import { registerRoutes } from './routes';
import config from './config'; // To ensure config is loaded, though not directly used here

// Ensure the custom declaration for reply.view is picked up
/// <reference path="./fastify.d.ts" />

const server: FastifyInstance = fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info', // Or your preferred logging level
  }
});

// Register Fastify plugins
server.register(fastifyView, {
  engine: {
    ejs: ejs,
  },
  root: path.join(__dirname, '../views'),
  viewExt: 'ejs',
  options: {
    // Add any EJS options here if needed
  }
});

server.register(fastifyFormbody);
server.register(fastifyStatic, {
  root: path.join(__dirname, '../public'),
  prefix: '/public/',
});
server.register(fastifyMultipart);

// Register routes
registerRoutes(server);

// Start Server
const start = async () => {
  try {
    const port = parseInt(process.env.PORT || '3000', 10);
    const host = process.env.HOST || '0.0.0.0';
    await server.listen({ port, host });
    // server.log.info(`Server listening on ${server.server.address()?.toString()}`); // More robust way to get address
    // Fastify's logger will output the listening address by default with logger:true
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

start();