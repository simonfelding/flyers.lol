/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Event } from '../models/Event';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Create a new event
     * Adds a new event to the system.
     * @param formData Event object to be added
     * @returns Event Event created successfully
     * @throws ApiError
     */
    public static createEvent(
        formData: {
            /**
             * A JSON string representing the Event object (excluding vector embedding).
             */
            event: string;
            /**
             * The event image file (optional).
             */
            imageFile?: Blob;
        },
    ): CancelablePromise<Event> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/events',
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                400: `Invalid input`,
                500: `Internal server error`,
            },
        });
    }
}
