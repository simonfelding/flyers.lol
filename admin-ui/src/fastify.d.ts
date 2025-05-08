import { FastifyReply } from 'fastify';

declare module 'fastify' {
  interface FastifyReply {
    view(page: string, data?: object): FastifyReply;
  }
}