import config from '../config';
import FormData from 'form-data'; // Ensure FormData is available
import { Event, Error as ApiError } from '../generated-api-types'; // Assuming Event and ApiError types

/**
 * Submits event data (including an optional image file) to the event-ingest service.
 *
 * @param eventPayload The core event data (excluding id, version, etc.).
 * @param imageFile Optional image file data.
 * @returns The response from the event-ingest service.
 */
export async function submitEventToIngest(
  eventPayload: Omit<Event, 'id' | 'version' | 'signature' | 'vector_embedding' | 'related_links'> & { related_links?: Event['related_links'] },
  imageFile?: { buffer: Buffer; filename: string; mimetype: string }
): Promise<{ success: boolean; eventId?: string; error?: string; status?: number }> {
  const backendFormData = new FormData();
  const eventJsonString = JSON.stringify(eventPayload);
  backendFormData.append('event', eventJsonString);

  if (imageFile && imageFile.buffer.length > 0) {
    backendFormData.append('imageFile', imageFile.buffer, {
      filename: imageFile.filename,
      contentType: imageFile.mimetype,
    });
  }

  try {
    const fetchResponse = await fetch(config.EVENT_INGEST_URL, { // Using EVENT_INGEST_URL from config
      method: 'POST',
      body: backendFormData as any, // FormData is correctly handled by fetch
    });

    const responseText = await fetchResponse.text();

    if (!fetchResponse.ok) {
      let errorDetail = responseText;
      try {
        const errorJson = JSON.parse(responseText) as ApiError;
        if (errorJson.message) errorDetail = errorJson.message;
      } catch (e) { /* ignore parsing error, use raw text */ }
      return { success: false, error: `Event Ingest failed: ${errorDetail}`, status: fetchResponse.status };
    }

    const responseData = JSON.parse(responseText);
    if (responseData && responseData.event_id) {
      return { success: true, eventId: responseData.event_id, status: fetchResponse.status };
    } else {
      return { success: false, error: 'Event ingest service responded successfully but did not return an event ID.', status: 500 };
    }
  } catch (error: any) {
    console.error("Error submitting event to ingest service:", error);
    return { success: false, error: error.message || 'Failed to connect to event ingest service.', status: 500 };
  }
}