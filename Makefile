.PHONY: generate-api-code
generate-api-code:
	@echo "Generating API code (Pydantic models) from openapi.yml... requires: python3 -m pip install --user 'datamodel-code-generator[openapi]'"
	python3 -m datamodel_code_generator --input openapi.yml --input-file-type openapi --output event-ingest/generated_models.py --use-title-as-name --capitalise-enum-members
	@echo "Pydantic models generated at event-ingest/generated_models.py"

.PHONY: generate-admin-ui-types
generate-admin-ui-types:
	@echo "Generating TypeScript interfaces for admin-ui from openapi.yml..."
	npx openapi-typescript-codegen --input ./openapi.yml --output ./admin-ui/src/generated-api-types --client fetch --useUnionTypes
	@echo "TypeScript interfaces generated at admin-ui/src/generated-api-types"

# Modify existing generate-api-code or add a new all target
.PHONY: generate-all-api-code
generate-all-api-code: generate-api-code generate-admin-ui-types