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
## Utility Scripts

### Adding a Random Test Event

A Python script is available to generate and submit a random, valid test event to the `event-ingest` service. This is useful for populating the development environment with test data.

**Prerequisites:**
*   The development services (including `event-ingest`) must be running. You can start them with:
    ```bash
    docker-compose up -d
    ```
*   Python 3 and `httpx` library installed in your environment. If `httpx` is not installed, you can install it via pip:
    ```bash
    pip install httpx
    ```

**Usage:**
To run the script, execute the following command from the project root:
```bash
python scripts/add_random_event.py
```

Alternatively, you can use the Makefile target:

```bash
make add-random-event
```

The script will output the generated event data, the status code of the submission, and the response from the server.
## Documentation

This project uses MkDocs with the Material theme for documentation.

To build and serve the documentation locally:
1. Install documentation dependencies: `pip install -r requirements-docs.txt`
2. Run `mkdocs serve` from the project root.
3. Open your browser to `http://127.0.0.1:8000`.

The documentation source files are located in the `docs/` directory.