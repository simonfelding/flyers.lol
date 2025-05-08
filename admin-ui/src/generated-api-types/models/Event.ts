/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ActionLink } from './ActionLink';
import type { Location } from './Location';
import type { Media } from './Media';
import type { OrganizerInfo } from './OrganizerInfo';
import type { RelatedLinkItem } from './RelatedLinkItem';
/**
 * Schema for event data structure
 */
export type Event = {
    /**
     * Semantic version of the event data structure (e.g., "1.0.0").
     */
    version: string;
    /**
     * Unique identifier for the event (e.g., "evt_xxxxxxxx").
     */
    id: string;
    /**
     * The main title or name of the event.
     */
    title: string;
    /**
     * A detailed description of the event.
     */
    description: string;
    /**
     * The start date and time of the event in ISO 8601 format.
     */
    start_time: string;
    /**
     * The end date and time of the event in ISO 8601 format. Optional.
     */
    end_time?: string;
    location: Location;
    organizer_info: OrganizerInfo;
    action_link?: ActionLink;
    /**
     * Cryptographic signature of the event data from the original creator.
     */
    signature: string;
    media?: Media;
    /**
     * An array of general-purpose links related to the event. Optional.
     */
    related_links?: Array<RelatedLinkItem>;
    /**
     * Vector embedding of the event's content. Optional at creation.
     */
    vector_embedding?: Array<number>;
};

