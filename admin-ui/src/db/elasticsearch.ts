import { Client, errors as EsErrors } from '@elastic/elasticsearch';
import { SearchResponse, GetResponse, DeleteResponse } from '@elastic/elasticsearch/lib/api/types';
import config from '../config';
import { Event } from '../generated-api-types'; // Assuming Event is the primary type for documents

// Initialize Elasticsearch Client
const esClient = new Client({ node: config.ELASTICSEARCH_URL });

/**
 * Fetches all events from Elasticsearch, sorted by start_time.
 */
export async function getAllEvents(): Promise<(Event & { _id: string })[]> {
  const response: SearchResponse<Event> = await esClient.search<Event>({
    index: 'events',
    query: {
      match_all: {},
    },
    sort: [
      { "start_time": "asc" }
    ]
  });
  // Assuming _source is always present and includes the 'id' field as per Event type
  // Also, map _id from Elasticsearch to the event object if needed, or rely on event.id from _source
  return response.hits.hits.map((hit) => ({ ...hit._source, _id: hit._id } as Event & { _id: string }));
}

/**
 * Fetches a single event by its ID from Elasticsearch.
 * @param id The ID of the event to fetch.
 * @returns The event document or null if not found.
 */
export async function getEventById(id: string): Promise<(Event & { _id: string }) | null> {
  try {
    const response: GetResponse<Event> = await esClient.get<Event>({
      index: 'events',
      id,
    });
    if (response._source) {
      return { ...response._source, _id: response._id } as Event & { _id: string };
    }
    return null;
  } catch (error) {
    if (error instanceof EsErrors.ResponseError && error.statusCode === 404) {
      return null; // Event not found
    }
    throw error; // Re-throw other errors
  }
}

/**
 * Updates an existing event in Elasticsearch.
 * @param id The ID of the event to update.
 * @param eventData The partial event data to update.
 */
export async function updateEvent(id: string, eventData: Partial<Omit<Event, 'id' | 'version' | 'signature' | 'vector_embedding'>>): Promise<void> {
  await esClient.update<Event, Partial<Omit<Event, 'id' | 'version' | 'signature' | 'vector_embedding'>>>({
    index: 'events',
    id,
    doc: eventData,
  });
}

/**
 * Deletes an event by its ID from Elasticsearch.
 * @param id The ID of the event to delete.
 */
export async function deleteEvent(id: string): Promise<DeleteResponse> {
  return esClient.delete({
    index: 'events',
    id,
  });
}

// Export the client if it needs to be used directly elsewhere, though typically functions are preferred.
export { esClient, EsErrors };