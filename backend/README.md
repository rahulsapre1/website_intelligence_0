# Website Intelligence Backend

AI-powered website analysis and conversational interface backend built with FastAPI.

## Features

- **Hybrid Web Scraping**: Primary scraper (httpx + BeautifulSoup) with Jina AI fallback for JS-heavy sites
- **AI-Powered Analysis**: Google Gemini 2.5 Flash for business insight extraction
- **Conversational Interface**: Context-aware chat about analyzed websites
- **Vector Search**: Semantic search using Gemini embeddings and Qdrant
- **Rate Limiting**: Built-in rate limiting with slowapi
- **Comprehensive Testing**: Unit and integration tests with 80%+ coverage

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `API_SECRET_KEY`: Secret key for API authentication
- `GEMINI_API_KEY`: Google Gemini API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `QDRANT_URL`: Qdrant Cloud URL
- `QDRANT_API_KEY`: Qdrant API key (optional for free tier)

### 3. Run the Application

```bash
# Development mode
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## API Endpoints

### POST /api/v1/analyze
Analyze a website and extract business insights.

**Request:**
```json
{
  "url": "https://example.com",
  "questions": ["What is your pricing model?"]  // optional
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "url": "https://example.com",
  "insights": {
    "industry": "SaaS",
    "company_size": "Medium",
    "location": "San Francisco",
    "usp": "AI-powered analytics platform",
    "products_services": ["Analytics", "Reporting"],
    "target_audience": "B2B enterprises",
    "contact_info": {
      "email": "contact@example.com",
      "phone": "+1-555-123-4567"
    }
  },
  "custom_answers": ["Subscription-based pricing"],
  "fallback_used": false
}
```

### POST /api/v1/chat
Ask questions about a previously analyzed website.

**Request:**
```json
{
  "session_id": "uuid",  // or "url": "https://example.com"
  "query": "Tell me more about their pricing model",
  "conversation_history": []  // optional
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "answer": "Based on the homepage content, they offer subscription-based pricing...",
  "sources": ["Chunk 1: Pricing information...", "Chunk 2: Plans details..."],
  "follow_up_suggestions": [
    "What are their main competitors?",
    "How long have they been in business?"
  ]
}
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

## Architecture

### Core Components

1. **Web Scraping Layer**
   - Primary: httpx + BeautifulSoup4
   - Fallback: Jina AI Reader API
   - Smart content quality detection

2. **AI Processing Layer**
   - Google Gemini 2.5 Flash for extraction
   - Gemini text-embedding-004 for embeddings
   - Structured prompt engineering

3. **Data Storage Layer**
   - Supabase PostgreSQL for sessions/conversations
   - Qdrant Cloud for vector embeddings
   - Simple caching via database lookup

4. **API Layer**
   - FastAPI with async/await
   - Pydantic validation
   - Rate limiting with slowapi
   - Comprehensive error handling

### Performance Optimizations

- Async operations throughout
- Parallel scraping + embedding generation
- Database-based caching (1-hour TTL)
- Configurable content quality thresholds
- Smart fallback detection

## Configuration

Key configuration options in `.env`:

```bash
# Scraping thresholds
MIN_TEXT_LENGTH=500
MIN_TEXT_RATIO=0.1
MIN_KEYWORD_MATCHES=2

# Rate limiting
ANALYZE_RATE_LIMIT=10/minute
CHAT_RATE_LIMIT=30/minute

# Logging
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Configuration and security
│   ├── middleware/      # Auth and rate limiting
│   ├── models/          # Pydantic models
│   ├── prompts/         # AI prompt templates
│   ├── services/        # Business logic
│   └── utils/           # Utilities
├── tests/               # Test suite
├── requirements.txt     # Dependencies
└── README.md           # This file
```

### Adding New Features

1. **New API Endpoint**: Add to `app/api/v1/`
2. **New Service**: Add to `app/services/`
3. **New Model**: Add to `app/models/`
4. **New Test**: Add to `tests/`

### Code Quality

- Type hints throughout
- Comprehensive error handling
- Async/await for I/O operations
- Pydantic validation
- 80%+ test coverage

## Deployment

### Docker

```bash
# Build image
docker build -t website-intelligence-backend .

# Run container
docker run -p 8000:8000 --env-file .env website-intelligence-backend
```

### Environment Variables for Production

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
API_SECRET_KEY=your_secure_secret_key
# ... other variables
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics

- Request/response times
- Scraping success rates
- AI processing times
- Database connection status
- Vector store status

## Troubleshooting

### Common Issues

1. **Scraping Failures**: Check if fallback scraper is configured
2. **AI Processing Errors**: Verify Gemini API key and quota
3. **Database Connection**: Check Supabase credentials
4. **Vector Store Issues**: Verify Qdrant connection

### Logs

Check application logs for detailed error information:

```bash
# Development
tail -f app.log

# Production
docker logs website-intelligence-backend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
