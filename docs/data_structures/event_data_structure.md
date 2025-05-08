# Event Data Structure

This document describes the data structure for representing events within the system. The formal and canonical definition of the event structure and related API endpoints is provided in the OpenAPI specification: [`openapi.yml`](../../openapi.yml).

## 1. Design Rationale & Structure Overview

The design of this event data structure has undergone several iterations to balance comprehensiveness with simplicity, and to ensure essential information is captured effectively.

Key decisions include:
*   **Core Information**: Fields like `id`, `version`, `title`, `description`, `start_time`, and `location` are fundamental and required.
*   **Organizer Information**: The `organizer_info` object is required, with `organizer_info.name` being a required field within it. Systems can default `organizer_info.name` to "Unknown" if not provided by the event creator, ensuring the field's presence.
*   **Actionability**: An optional `action_link` allows for direct calls to action (e.g., ticket purchase).
*   **Media Handling**: The `media` object is optional and designed to be flexible. At creation, it can accept an embedded media blob via a Data URI in `media.value`. Post-creation, this is expected to be converted by the system to a URL or CID for efficient storage and retrieval. The `media.type` field specifies whether it's an image or video.
*   **Creator Verification**: A `signature` field is included for the original creator to sign the event data, ensuring authenticity.
*   **Extensibility & Search**: A `vector_embedding` field is included. While optional at creation, it's intended to be populated by the system (e.g., by an NLP service) to facilitate semantic search and discovery.
*   **Simplicity**: Fields like `tags`, generic `metadata`, `created_at`, and `updated_at` were initially considered but removed to streamline the core structure, focusing on essential event properties.

## 2. Structure Reference

For the definitive schema of the `Event` object and its components (`Location`, `OrganizerInfo`, `ActionLink`, `Media`, `Geo`, `RelatedLinkItem`), please refer to the `components.schemas` section in the [OpenAPI specification file (`openapi.yml`)](../../openapi.yml).

The OpenAPI specification provides:
*   Data types for each field.
*   Required vs. optional fields.
*   Formatting constraints (e.g., `date-time`, `uri`, `email`).
*   Enumerated values where applicable.
*   Example values.

## 3. Detailed Field Descriptions (Contextual Overview)

| Field Path             | Data Type         | Required?                                  | Description                                                                                                                               |
|------------------------|-------------------|--------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `version`              | string            | **Yes**                                    | Semantic version of the event data structure (e.g., "1.0.0").                                                                             |
| `id`                   | string            | **Yes**                                    | Unique identifier for the event (e.g., "evt_xxxxxxxx").                                                                                   |
| `title`                | string            | **Yes**                                    | The main title or name of the event.                                                                                                      |
| `description`          | string            | **Yes**                                    | A detailed description of the event.                                                                                                      |
| `start_time`           | string (ISO 8601) | **Yes**                                    | The start date and time of the event in ISO 8601 format (e.g., "2024-10-26T09:00:00Z").                                                  |
| `end_time`             | string (ISO 8601) | No                                         | The end date and time of the event in ISO 8601 format. Optional.                                                                          |
| `location`             | object            | **Yes**                                    | Object containing location details for the event.                                                                                         |
| `location.name`        | string            | **Yes** (within `location`)                | Name of the venue or a general location description (e.g., "Online", "Community Hall").                                                   |
| `location.address`     | string            | No                                         | Full street address of the event location.                                                                                                |
| `location.geo`         | object            | No                                         | Geographical coordinates.                                                                                                                 |
| `location.geo.latitude`| number            | Required if `geo` object is present        | Latitude of the event location.                                                                                                           |
| `location.geo.longitude`| number           | Required if `geo` object is present        | Longitude of the event location.                                                                                                          |
| `organizer_info`       | object            | **Yes**                                    | Object containing information about the event organizer.                                                                                  |
| `organizer_info.name`  | string            | **Yes** (within `organizer_info`)          | Name of the organizer. Can default to "Unknown" if not provided by the creator.                                                           |
| `organizer_info.contact_email` | string   | No                                         | Contact email address for the organizer.                                                                                                  |
| `organizer_info.website`| string            | No                                         | Website URL for the organizer.                                                                                                            |
| `action_link`          | object            | No                                         | An object representing a primary call-to-action link for the event.                                                                       |
| `action_link.url`      | string            | Required if `action_link` object is present| The URL for the action (e.g., ticket purchase, RSVP page).                                                                                |
| `action_link.text`     | string            | Required if `action_link` object is present| Display text for the action link (e.g., "Buy Tickets", "RSVP Here").                                                                      |
| `action_link.type`     | string            | No                                         | Type of action (e.g., "purchase", "rsvp", "register", "info").                                                                            |
| `signature`            | string            | **Yes**                                    | Cryptographic signature of the event data from the original creator, ensuring authenticity and integrity.                                 |
| `media`                | object            | No                                         | Optional object for event-related media (image or video).                                                                                 |
| `media.type`           | string            | Required if `media` object is present      | Type of media, e.g., "image", "video".                                                                                                    |
| `media.value`          | string            | Required if `media` object is present      | The media content itself. At creation, can be a Data URI (e.g., `data:image/png;base64,...`). Post-creation, expected to be a URL or CID. |
| `related_links`        | array of objects  | No                                         | An array of general-purpose links related to the event (e.g., agenda, speaker bios, social media).                                        |
| `related_links[].url`  | string            | Required if `related_links` object is present | The URL for the related link.                                                                                                             |
| `related_links[].text` | string            | Required if `related_links` object is present | Display text for the related link.                                                                                                        |
| `related_links[].type` | string            | No                                         | Type of related link (e.g., "info", "video", "social", "press").                                                                          |
| `vector_embedding`     | array of numbers  | No                                         | An array of numbers representing the vector embedding of the event's content. Optional at creation; can be populated by the system.      |

## 4. Versioning Strategy

The `version` field at the root of the JSON object uses Semantic Versioning (SemVer) MAJOR.MINOR.PATCH (e.g., "1.0.0", "1.1.0", "2.0.0").

*   **PATCH** version increments for backward-compatible bug fixes or clarifications (e.g., documentation updates that don't change structure).
*   **MINOR** version increments for adding new optional fields or functionality in a backward-compatible way. Consumers of older minor versions should still be able to process newer minor versions by ignoring unrecognized fields.
*   **MAJOR** version increments for any backward-incompatible changes to the structure (e.g., removing fields, changing data types of existing fields, making previously optional fields required).

This strategy allows consumers to understand the nature of changes between versions and adapt accordingly.