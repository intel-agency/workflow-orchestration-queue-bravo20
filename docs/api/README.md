# OS-APOW API Documentation

This directory contains API documentation for the OS-APOW system.

## Contents

- [Endpoints](./endpoints.md) - API endpoint reference
- [Webhooks](./webhooks.md) - Webhook payload schemas
- [Models](./models.md) - Data model reference

## Quick Reference

### Notifier Service (The Ear)

Base URL: `http://localhost:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | Service info |
| `/webhooks/github` | POST | GitHub webhook receiver |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc documentation |

### Authentication

Webhook endpoints require HMAC SHA256 signature validation via the `X-Hub-Signature-256` header.

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 202 | Accepted (webhook processed asynchronously) |
| 400 | Bad Request (invalid payload) |
| 401 | Unauthorized (invalid signature) |
| 500 | Internal Server Error |
