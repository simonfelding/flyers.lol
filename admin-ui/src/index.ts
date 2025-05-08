import fastify, { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { Client, errors as EsErrors } from '@elastic/elasticsearch';
import { SearchResponse, GetResponse } /*, UpdateResponse */ from '@elastic/elasticsearch/lib/api/types'; // UpdateResponse might not be needed if not directly used
import path from 'path';
import { Event, Location, OrganizerInfo, Media, ActionLink } from './generated-api-types';

// Ensure the custom declaration for reply.view is picked up
/// <reference path="./fastify.d.ts" />

const server: FastifyInstance = fastify({ logger: true });

// Register Fastify plugins
server.register(require('@fastify/view'), {
  engine: {
    ejs: require('ejs'),
  },
  root: path.join(__dirname, '../views'),
  viewExt: 'ejs',
  options: {
    // Add any EJS options here if needed
  }
});

server.register(require('@fastify/formbody'));
server.register(require('@fastify/static'), {
  root: path.join(__dirname, '../public'),
  prefix: '/public/',
});

// Initialize Elasticsearch Client
const ELASTICSEARCH_URL = process.env.ELASTICSEARCH_URL || 'http://localhost:9200';
const esClient = new Client({ node: ELASTICSEARCH_URL });
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000'; // Default for event-ingest

// Type for request parameters with an ID
interface IdParam {
  id: string;
}

// Type for event body from forms
interface EventFormData {
  title: string;
  description: string;
  start_time: string; // ISO 8601 format
  end_time?: string;   // ISO 8601 format
  location_name: string;
  location_address?: string;
  location_geo_latitude?: string;
  location_geo_longitude?: string;
  organizer_name: string;
  organizer_contact_email?: string;
  organizer_website?: string;
  media_type?: 'image' | 'video';
  media_value?: string;
  action_link_url?: string;
  action_link_text?: string;
  action_link_type?: string;
}

function getLocationFromFormData(data: EventFormData): Location {
    const location: Location = { name: data.location_name };
    if (data.location_address) location.address = data.location_address;
    const lat = parseFloat(data.location_geo_latitude || '');
    const lon = parseFloat(data.location_geo_longitude || '');
    if (!isNaN(lat) && !isNaN(lon)) {
        location.geo = { latitude: lat, longitude: lon };
    }
    return location;
}

function getOrganizerInfoFromFormData(data: EventFormData): OrganizerInfo {
    const organizer: OrganizerInfo = { name: data.organizer_name };
    if (data.organizer_contact_email) organizer.contact_email = data.organizer_contact_email;
    if (data.organizer_website) organizer.website = data.organizer_website;
    return organizer;
}

function getMediaFromFormData(data: EventFormData): Media | undefined {
    if (data.media_type && data.media_value) {
        let mediaTypeToAssign: Media["type"];
        if (data.media_type === 'image' || data.media_type === 'video') {
            mediaTypeToAssign = data.media_type;
        } else {
            // This case should ideally not happen if form validation is correct
            // or if media_type is strictly 'image' | 'video'
            // For robustness, log an error or handle as appropriate
            console.error(`Invalid media_type encountered: ${data.media_type}`);
            return undefined; // Or throw an error
        }
        return { type: mediaTypeToAssign, value: data.media_value };
    }
    return undefined;
}

function getActionLinkFromFormData(data: EventFormData): ActionLink | undefined {
    if (data.action_link_url && data.action_link_text) {
        const link: ActionLink = { url: data.action_link_url, text: data.action_link_text };
        if (data.action_link_type) link.type = data.action_link_type;
        return link;
    }
    return undefined;
}

// Routes

// GET / - List Events
server.get('/', async (request: FastifyRequest, reply: FastifyReply) => {
  let events: any[] = []; // Default to empty list
  let fetchError: string | null = null; // Default to no error

  try {
    const response: SearchResponse<Event> = await esClient.search<Event>({
      index: 'events',
      query: {
        match_all: {},
      },
      sort: [
        { "start_time": "asc" }
      ]
    });
    // Assuming _source is always present for matched documents and includes the 'id' field as per Event type
    events = response.hits.hits.map((hit) => ({ ...hit._source, _id: hit._id })); // Use _id for ES document ID
  } catch (error) {
    server.log.error("Failed to fetch events from Elasticsearch:", error);
    fetchError = "Could not load events from the database."; // Set error message for the template
    // Do NOT send an error reply here, proceed to render the template
  }

  // Always render the template, passing events (possibly empty) and any error message
  return reply.view('index', {
    events: events,
    error: fetchError, // Pass the error message to the template
    API_BASE_URL: API_BASE_URL // Ensure API_BASE_URL is passed
  });
});

// GET /event/:id - View Event
server.get('/event/:id', async (request: FastifyRequest<{ Params: IdParam }>, reply: FastifyReply) => {
  const { id } = request.params;
  try {
    const response: GetResponse<Event> = await esClient.get<Event>({
      index: 'events',
      id,
    });
    if (!response._source) {
      return reply.status(404).send({ error: 'Event not found' });
    }
    // _source is the event document. The Event type includes 'id'.
    // We pass the ES document _id separately if needed by the view, or rely on event.id from _source.
    const event = { ...response._source, _id: response._id };
    return reply.view('event-detail', { event });
  } catch (error) {
    server.log.error(`Error fetching event ${id} from Elasticsearch:`, error);
    if (error instanceof EsErrors.ResponseError && error.statusCode === 404) {
      return reply.status(404).send({ error: 'Event not found' });
    }
    return reply.status(500).send({ error: 'Failed to fetch event' });
  }
});

// GET /event/:id/edit - Show Edit Form
server.get('/event/:id/edit', async (request: FastifyRequest<{ Params: IdParam }>, reply: FastifyReply) => {
  const { id } = request.params;
  try {
    const response: GetResponse<Event> = await esClient.get<Event>({
      index: 'events',
      id,
    });
    if (!response._source) {
      return reply.status(404).send({ error: 'Event not found' });
    }
    const source = response._source;
    const eventFormData: EventFormData = {
        title: source.title,
        description: source.description,
        start_time: source.start_time,
        end_time: source.end_time,
        location_name: source.location.name,
        location_address: source.location.address,
        location_geo_latitude: source.location.geo?.latitude?.toString(),
        location_geo_longitude: source.location.geo?.longitude?.toString(),
        organizer_name: source.organizer_info.name,
        organizer_contact_email: source.organizer_info.contact_email,
        organizer_website: source.organizer_info.website,
        media_type: source.media?.type,
        media_value: source.media?.value,
        action_link_url: source.action_link?.url,
        action_link_text: source.action_link?.text,
        action_link_type: source.action_link?.type,
    };
    return reply.view('edit-event', { event: eventFormData, eventId: id });
  } catch (error) {
    server.log.error(`Error fetching event ${id} for editing:`, error);
    if (error instanceof EsErrors.ResponseError && error.statusCode === 404) {
      return reply.status(404).send({ error: 'Event not found' });
    }
    return reply.status(500).send({ error: 'Failed to fetch event for editing' });
  }
});

// POST /event/:id - Update Event
server.post('/event/:id', async (request: FastifyRequest<{ Params: IdParam; Body: EventFormData }>, reply: FastifyReply) => {
  const { id } = request.params;
  const formData = request.body;

  if (!formData.title || !formData.start_time || !formData.location_name || !formData.organizer_name) {
    return reply.status(400).send({ error: 'Title, Start Time, Location Name, and Organizer Name are required' });
  }

  try {
    const docToUpdate: Partial<Omit<Event, 'id' | 'version' | 'signature' | 'vector_embedding'>> = {
      title: formData.title,
      description: formData.description,
      start_time: formData.start_time,
      end_time: formData.end_time || undefined,
      location: getLocationFromFormData(formData),
      organizer_info: getOrganizerInfoFromFormData(formData),
      media: getMediaFromFormData(formData),
      action_link: getActionLinkFromFormData(formData),
    };

    // Type arguments for esClient.update: <TDocument, TPartialDocument>
    // TDocument is the full document type (Event)
    // TPartialDocument is the type of the partial document being sent for update
    await esClient.update<Event, Partial<Omit<Event, 'id' | 'version' | 'signature' | 'vector_embedding'>>>({
      index: 'events',
      id,
      doc: docToUpdate, // The 'doc' property should be at the top level of the update request body for partial updates
    });
    return reply.redirect(`/event/${id}`);
  } catch (error) {
    server.log.error(`Error updating event ${id} in Elasticsearch:`, error);
    if (error instanceof EsErrors.ResponseError && error.statusCode === 404) {
      return reply.status(404).send({ error: 'Event not found for update' });
    }
    return reply.status(500).send({ error: 'Failed to update event' });
  }
});

// POST /submit-event - Create Event
server.post('/submit-event', async (request: FastifyRequest<{ Body: EventFormData }>, reply: FastifyReply) => {
  const formData = request.body;

  if (!formData.title || !formData.start_time || !formData.location_name || !formData.organizer_name) {
    return reply.status(400).send({ error: 'Title, Start Time, Location Name, and Organizer Name are required for new event' });
  }

  try {
    const newEventIngestPayload: Omit<Event, 'id' | 'version' | 'signature' | 'vector_embedding' | 'related_links'> & { related_links?: Event['related_links'] } = {
      title: formData.title,
      description: formData.description || '',
      start_time: formData.start_time,
      end_time: formData.end_time || undefined,
      location: getLocationFromFormData(formData),
      organizer_info: getOrganizerInfoFromFormData(formData),
      media: getMediaFromFormData(formData),
      action_link: getActionLinkFromFormData(formData),
    };

    const apiUrl = `${API_BASE_URL}/events`;
    const fetchResponse = await fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(newEventIngestPayload),
    });

    if (!fetchResponse.ok) {
        const errorBody = await fetchResponse.text();
        server.log.error(`Error from event-ingest: ${fetchResponse.status} ${fetchResponse.statusText}`, errorBody);
        // It's good practice to inform the user about the failure.
        // Consider if you want to parse errorBody if it's JSON and show a more specific message.
        return reply.status(fetchResponse.status).send({ error: `Failed to create event: ${fetchResponse.statusText}. ${errorBody}` });
    }

    // Assuming the event-ingest service returns the created event or an ID.
    // If it returns the event ID in a specific format, adjust here.
    // For now, just redirecting on success.
    // const responseData = await fetchResponse.json(); // If you need to process the response
    return reply.redirect('/');
  } catch (error: any) {
    server.log.error('Error submitting event:', error.message);
    // Generic error for fetch or other types of issues
    return reply.status(500).send({ error: error.message || 'An unexpected error occurred while creating event' });
  }
});

// Start Server
const start = async () => {
  try {
    await server.listen({ port: 3000, host: '0.0.0.0' });
    console.log(`Server listening on http://localhost:3000 or http://<your-ip>:3000`);
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

start();