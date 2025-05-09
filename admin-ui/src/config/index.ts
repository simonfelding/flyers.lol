import dotenv from 'dotenv';

dotenv.config();

const config = {
  API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  ELASTICSEARCH_URL: process.env.ELASTICSEARCH_URL || 'http://localhost:9200',
  EVENT_INGEST_URL: process.env.EVENT_INGEST_URL || 'http://localhost:8080/v1/events', // Added for event ingest service
};

export default config;