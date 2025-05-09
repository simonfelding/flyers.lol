import { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { EsErrors, getAllEvents, getEventById, updateEvent } from '../db/elasticsearch';
import { submitEventToIngest } from '../services/eventIngest';
import { Event, Location, OrganizerInfo, Media, ActionLink, Error as ApiError } from '../generated-api-types';
import config from '../config'; // For API_BASE_URL, EVENT_INGEST_URL etc.
// FormData is used by submitEventToIngest, but not directly constructed here unless re-implementing parts of it.

// Type for request parameters with an ID
interface IdParam {
  id: string;
}

// Type for event body from forms (could be refined or moved to a shared types file if used elsewhere)
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
  media_value?: string; // URL for existing media
  action_link_url?: string;
  action_link_text?: string;
  action_link_type?: string;
  // imageFile field is handled by multipart, not directly in EventFormData
}

// Helper functions (moved from original index.ts)
function getLocationFromFormData(data: EventFormData): Location {
    const location: Location = { name: data.location_name };
    if (data.location_address) location.address = data.location_address;
    const lat = parseFloat(data.location_geo_latitude || '');
    const lon = parseFloat(data.location_geo_longitude || '');
    if (!isNaN(lat) && !isNaN(lon)) {
        location.geo = { lat: lat, lon: lon };
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
            console.error(`Invalid media_type encountered: ${data.media_type}`);
            return undefined;
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


export async function registerRoutes(fastify: FastifyInstance) {

  // GET / - List Events
  fastify.get('/', async (request: FastifyRequest, reply: FastifyReply) => {
    let events: (Event & { _id: string })[] = [];
    let fetchError: string | null = null;
    let message: { type?: string, text?: string, eventId?: string } | null = null;

    if (request.query && typeof request.query === 'object') {
      const query = request.query as { message?: string; eventId?: string; error?: string };
      if (query.message === 'success' && query.eventId) {
        message = { type: 'success', text: `Event successfully submitted! Event ID: ${query.eventId}`, eventId: query.eventId };
      } else if (query.error) {
        message = { type: 'error', text: query.error };
      }
    }

    try {
      events = await getAllEvents();
    } catch (error) {
      fastify.log.error("Failed to fetch events from Elasticsearch:", error);
      fetchError = "Could not load events from the database.";
    }

    return reply.view('index', {
      events: events,
      error: fetchError,
      message: message,
      API_BASE_URL: config.API_BASE_URL // Use config
    });
  });

  // GET /upload - Show Upload Event Form
  fastify.get('/upload', async (request: FastifyRequest, reply: FastifyReply) => {
    let message: { type?: string, text?: string } | null = null;
    if (request.query && typeof request.query === 'object') {
      const query = request.query as { error?: string };
      if (query.error) {
        message = { type: 'error', text: query.error };
      }
    }
    return reply.view('upload-event', { API_BASE_URL: config.API_BASE_URL, message });
  });

  // GET /event/:id - View Event
  fastify.get('/event/:id', async (request: FastifyRequest<{ Params: IdParam }>, reply: FastifyReply) => {
    const { id } = request.params;
    try {
      const event = await getEventById(id);
      if (!event) {
        return reply.status(404).send({ error: 'Event not found' });
      }
      return reply.view('event-detail', { event });
    } catch (error) {
      fastify.log.error(`Error fetching event ${id} from Elasticsearch:`, error);
      if (error instanceof EsErrors.ResponseError && error.statusCode === 404) { // EsErrors imported from db module
        return reply.status(404).send({ error: 'Event not found' });
      }
      return reply.status(500).send({ error: 'Failed to fetch event' });
    }
  });

  // GET /event/:id/edit - Show Edit Form
  fastify.get('/event/:id/edit', async (request: FastifyRequest<{ Params: IdParam }>, reply: FastifyReply) => {
    const { id } = request.params;
    try {
      const eventResult = await getEventById(id); // eventResult includes _id
      if (!eventResult) {
        return reply.status(404).send({ error: 'Event not found' });
      }
      // Map to EventFormData, eventResult is the full Event from DB
      const source = eventResult; // eventResult is the event object itself
      const eventFormData: EventFormData = {
          title: source.title,
          description: source.description,
          start_time: source.start_time,
          end_time: source.end_time,
          location_name: source.location.name,
          location_address: source.location.address,
          location_geo_latitude: source.location.geo?.lat?.toString(),
          location_geo_longitude: source.location.geo?.lon?.toString(),
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
      fastify.log.error(`Error fetching event ${id} for editing:`, error);
      if (error instanceof EsErrors.ResponseError && error.statusCode === 404) {
        return reply.status(404).send({ error: 'Event not found' });
      }
      return reply.status(500).send({ error: 'Failed to fetch event for editing' });
    }
  });

  // POST /event/:id - Update Event
  fastify.post('/event/:id', async (request: FastifyRequest<{ Params: IdParam; Body: EventFormData }>, reply: FastifyReply) => {
    const { id } = request.params;
    const formData = request.body;

    if (!formData.title || !formData.start_time || !formData.location_name || !formData.organizer_name) {
      // Consider rendering the edit form again with an error message
      return reply.status(400).view('edit-event', {
        event: formData,
        eventId: id,
        error: 'Title, Start Time, Location Name, and Organizer Name are required'
      });
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

      await updateEvent(id, docToUpdate);
      return reply.redirect(`/event/${id}?message=updated`); // Add a query param for feedback
    } catch (error) {
      fastify.log.error(`Error updating event ${id} in Elasticsearch:`, error);
      let errorMessage = 'Failed to update event';
      if (error instanceof EsErrors.ResponseError && error.statusCode === 404) {
        errorMessage = 'Event not found for update';
      }
      // Render edit form with error
      return reply.status(error instanceof EsErrors.ResponseError && error.statusCode === 404 ? 404 : 500)
                  .view('edit-event', { event: formData, eventId: id, error: errorMessage });
    }
  });

  // POST /submit-event - Create Event (handles multipart/form-data)
  fastify.post(
    '/submit-event',
    async (request: FastifyRequest, reply: FastifyReply) => {
      const parts = request.parts();
      const eventDataFields: Record<string, any> = {};
      let imageFile: { buffer: Buffer; filename: string; mimetype: string } | null = null;

      try {
        for await (const part of parts) {
          if (part.type === 'file' && part.fieldname === 'imageFile') {
            if (part.file && part.filename) {
              const chunks = [];
              for await (const chunk of part.file) {
                chunks.push(chunk);
              }
              if (chunks.length > 0) {
                imageFile = {
                  buffer: Buffer.concat(chunks),
                  filename: part.filename,
                  mimetype: part.mimetype,
                };
              }
            }
          } else if (part.type === 'field') {
            eventDataFields[part.fieldname] = typeof part.value === 'string' ? part.value : '';
          }
        }

        if (!eventDataFields.title || !eventDataFields.start_time || !eventDataFields.location_name || !eventDataFields.organizer_name) {
          return reply.status(400).send({ success: false, error: 'Title, Start Time, Location Name, and Organizer Name are required.' });
        }

        const typedEventDataFields = eventDataFields as EventFormData;
        const newEventPayload: Omit<Event, 'id' | 'version' | 'signature' | 'vector_embedding' | 'related_links'> & { related_links?: Event['related_links'] } = {
          title: typedEventDataFields.title,
          description: typedEventDataFields.description || '',
          start_time: typedEventDataFields.start_time,
          end_time: typedEventDataFields.end_time || undefined,
          location: getLocationFromFormData(typedEventDataFields),
          organizer_info: getOrganizerInfoFromFormData(typedEventDataFields),
          media: getMediaFromFormData(typedEventDataFields),
          action_link: getActionLinkFromFormData(typedEventDataFields),
        };

        const ingestResponse = await submitEventToIngest(newEventPayload, imageFile || undefined);

        if (ingestResponse.success && ingestResponse.eventId) {
          // For client-side handling (e.g., SPA or JS-enhanced form)
          // If redirecting, use: reply.redirect(`/?message=success&eventId=${ingestResponse.eventId}`);
          reply.send({ success: true, eventId: ingestResponse.eventId });
        } else {
          fastify.log.error('Event submission failed or missing event_id from ingest service:', ingestResponse);
          reply.status(ingestResponse.status || 500).send({ success: false, error: ingestResponse.error || 'Failed to submit event to ingest service.' });
        }

      } catch (error: any) {
        fastify.log.error("Error processing event submission in /submit-event route:", error);
        reply.status(500).send({ success: false, error: error.message || 'Failed to process event submission.' });
      }
    }
  );
}