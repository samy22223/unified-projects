# API Documentation

This directory contains comprehensive documentation for the Pinnacle AI Platform API.

## 📋 Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Versions](#api-versions)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
- [Webhooks](#webhooks)
- [SDKs](#sdks)
- [Examples](#examples)
- [Testing](#testing)

## 🚀 Overview

The Pinnacle AI Platform API provides programmatic access to all platform features including AI agents, e-commerce functionality, dropshipping automation, and third-party integrations.

### Base URL

```
https://api.pinnacle-ai.com
```

### API Versions

- **v1** (Current): Latest stable version
- **v1beta**: Beta features and endpoints

### Content Types

- Request: `application/json`
- Response: `application/json`

### Request Format

```bash
curl -X GET "https://api.pinnacle-ai.com/api/v1/agents" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include your API key in the Authorization header:

```bash
Authorization: Bearer YOUR_API_KEY
```

### Getting an API Key

1. Sign up for a Pinnacle AI Platform account
2. Navigate to the API settings in your dashboard
3. Generate a new API key
4. Use the key in your requests

### API Key Security

- Keep your API keys secure and never expose them in client-side code
- Use environment variables or secure key management systems
- Rotate your API keys regularly
- Monitor your API usage for suspicious activity

## 📊 Rate Limiting

Rate limits are applied per API key:

- **Requests per minute**: 1000
- **Requests per hour**: 10,000
- **Requests per day**: 100,000

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1634567890
```

### Handling Rate Limits

```python
import time
import requests

def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 429:  # Too Many Requests
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            sleep_time = max(reset_time - time.time(), 0) + 1
            time.sleep(sleep_time)
            continue

        return response

    raise Exception("Max retries exceeded")
```

## ❌ Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The provided API key is invalid or expired",
    "details": {
      "field": "api_key",
      "issue": "expired"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_1234567890"
  }
}
```

### Common HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **429**: Too Many Requests
- **500**: Internal Server Error

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_API_KEY` | API key is invalid or expired |
| `INSUFFICIENT_PERMISSIONS` | API key lacks required permissions |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `INVALID_REQUEST` | Request format is invalid |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `VALIDATION_ERROR` | Request data validation failed |
| `INTERNAL_ERROR` | Internal server error |

## 🛣️ Endpoints

### AI Agents

#### List Agents
```http
GET /api/v1/agents
```

#### Get Agent Details
```http
GET /api/v1/agents/{agent_id}
```

#### Create Agent
```http
POST /api/v1/agents
```

#### Update Agent
```http
PUT /api/v1/agents/{agent_id}
```

#### Delete Agent
```http
DELETE /api/v1/agents/{agent_id}
```

### E-commerce

#### List Stores
```http
GET /api/v1/ecommerce/stores
```

#### Get Store Details
```http
GET /api/v1/ecommerce/stores/{store_id}
```

#### Create Store
```http
POST /api/v1/ecommerce/stores
```

### Dropshipping

#### List Suppliers
```http
GET /api/v1/dropshipping/suppliers
```

#### Get Supplier Products
```http
GET /api/v1/dropshipping/suppliers/{supplier_id}/products
```

### Integrations

#### List Integrations
```http
GET /api/v1/integrations
```

#### Configure Integration
```http
POST /api/v1/integrations/{integration_type}/configure
```

## 🪝 Webhooks

Configure webhooks to receive real-time notifications about events in your platform.

### Webhook Events

- `agent.created`
- `agent.updated`
- `agent.deleted`
- `order.created`
- `order.updated`
- `order.fulfilled`
- `integration.connected`
- `integration.disconnected`

### Webhook Configuration

```bash
# Register webhook
curl -X POST "https://api.pinnacle-ai.com/api/v1/webhooks" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks",
    "events": ["order.created", "agent.updated"],
    "secret": "your-webhook-secret"
  }'
```

### Webhook Security

- Verify webhook signatures using the provided secret
- Use HTTPS for webhook URLs
- Implement retry logic for failed webhook deliveries

## 📦 SDKs

### Official SDKs

- **Python**: `pip install pinnacle-ai-platform`
- **JavaScript**: `npm install pinnacle-ai-platform`
- **PHP**: `composer require pinnacle-ai-platform/sdk`
- **Go**: `go get github.com/pinnacle-ai/platform-sdk`

### Python SDK Example

```python
from pinnacle_ai import PinnacleAI

client = PinnacleAI(api_key="your-api-key")

# List agents
agents = client.agents.list()

# Create an agent
agent = client.agents.create({
    "name": "Customer Support Agent",
    "type": "chatbot",
    "configuration": {
        "model": "gpt-4",
        "temperature": 0.7
    }
})
```

## 💡 Examples

### Basic Agent Creation

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "https://api.pinnacle-ai.com"

def create_agent():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "name": "Sales Assistant",
        "type": "chatbot",
        "configuration": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 150
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/agents",
        headers=headers,
        json=data
    )

    if response.status_code == 201:
        print("Agent created successfully!")
        print(response.json())
    else:
        print(f"Error: {response.status_code}")
        print(response.json())

create_agent()
```

### E-commerce Store Integration

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "https://api.pinnacle-ai.com"

def create_store():
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "name": "My Online Store",
        "platform": "shopify",
        "configuration": {
            "shopify_domain": "my-store.myshopify.com",
            "api_key": "your-shopify-api-key",
            "api_secret": "your-shopify-api-secret"
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/ecommerce/stores",
        headers=headers,
        json=data
    )

    return response.json()

store = create_store()
print(f"Store created: {store}")
```

## 🧪 Testing

### Postman Collection

Download our [Postman collection](https://api.pinnacle-ai.com/postman-collection) to test the API endpoints.

### API Testing Tools

- **Postman**: Complete API collection
- **Insomnia**: Alternative API client
- **curl**: Command-line testing
- **httpie**: User-friendly command-line HTTP client

### Test Environment

Use our sandbox environment for testing:

```bash
# Sandbox base URL
https://sandbox-api.pinnacle-ai.com

# Get sandbox API key from your dashboard
```

## 📞 Support

- **API Documentation**: [docs.pinnacle-ai.com](https://docs.pinnacle-ai.com)
- **Support Email**: api-support@pinnacle-ai.com
- **Community Forum**: [community.pinnacle-ai.com](https://community.pinnacle-ai.com)
- **Status Page**: [status.pinnacle-ai.com](https://status.pinnacle-ai.com)

## 🔄 Changelog

See our [API changelog](CHANGELOG.md) for information about API changes and updates.

---

For more information, visit our [developer portal](https://developers.pinnacle-ai.com).