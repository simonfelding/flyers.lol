## Development

This project uses an OpenAPI specification ([`openapi.yml`](openapi.yml:1)) as the single source of truth for the event API schema.
Pydantic models for the `event-ingest` service and TypeScript interfaces for the `admin-ui` service are generated from this specification.

### Modifying the API
If you make changes to the API definition in [`openapi.yml`](openapi.yml:1):
1.  Ensure you have Python 3 and `pip` installed.
2.  Run the following command from the project root to regenerate the Pydantic models and TypeScript interfaces:
    ```bash
    make generate-all-api-code
    ```
    Alternatively, you can generate them individually:
    *   For Pydantic models: `make generate-api-code`
    *   For `admin-ui` TypeScript types: `make generate-admin-ui-types`
3.  This will update `event-ingest/generated_models.py` and `admin-ui/src/generated-api-types.ts`.
4.  Commit the changes to [`openapi.yml`](openapi.yml:1) and the updated generated files (`event-ingest/generated_models.py` and `admin-ui/src/generated-api-types.ts`).

The CI pipeline includes a step to verify that the committed `event-ingest/generated_models.py` and `admin-ui/src/generated-api-types.ts` are consistent with [`openapi.yml`](openapi.yml:1). If they are out of sync, the build will fail.