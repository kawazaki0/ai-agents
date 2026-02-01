export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_LOGS_PROTOCOL=http/json
export OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://api.smith.langchain.com/otel/v1/claude_code
source .env
export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=$LANGSMITH_API_KEY,Langsmith-Project=claude_code"
cd agents_final
claude
