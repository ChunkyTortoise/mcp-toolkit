# API Guide

## Authentication

All API requests require a Bearer token in the Authorization header.

```
Authorization: Bearer <your-api-key>
```

## Endpoints

### GET /api/v1/resources
List all resources with pagination support.

**Parameters:**
- `page` (int): Page number, default 1
- `limit` (int): Items per page, default 20, max 100

**Response:**
```json
{
  "data": [...],
  "total": 150,
  "page": 1,
  "pages": 8
}
```

### POST /api/v1/resources
Create a new resource.

**Body:**
```json
{
  "name": "My Resource",
  "type": "document",
  "tags": ["important"]
}
```

### PUT /api/v1/resources/:id
Update an existing resource by ID.

### DELETE /api/v1/resources/:id
Delete a resource by ID. Returns 204 on success.

## Rate Limiting

API requests are limited to 100 per minute per API key. Rate limit headers are included in every response.

## Error Handling

Errors return JSON with `error` and `message` fields. Common status codes: 400 (bad request), 401 (unauthorized), 404 (not found), 429 (rate limited).
