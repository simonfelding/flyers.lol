/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Geo } from './Geo';
/**
 * Object containing location details for the event.
 */
export type Location = {
    /**
     * Name of the venue or a general location description.
     */
    name: string;
    /**
     * Full street address of the event location. Optional.
     */
    address?: string;
    geo?: Geo;
};

