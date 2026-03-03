# FastAPI Documentation

## Overview

The Prescription Processing System now includes a **FastAPI** framework for exposing the ML models as REST API endpoints. This allows easy integration with web applications, mobile apps, and external systems.

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The updated `requirements.txt` includes:
- `fastapi==0.104.1` - Modern web framework
- `uvicorn==0.24.0` - ASGI server
- `pydantic==2.5.0` - Data validation

### 2. Run the API Server

```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or using Python
python main.py

# Or using Python module
python -m uvicorn main:app --reload
```

The server will start at `http://localhost:8000`

## API Endpoints

### Health & Status Endpoints

#### 1. **Health Check**
- **URL**: `GET /health`
- **Description**: Simple health check
- **Response**:
  ```json
  {
    "status": "healthy",
    "message": "Prescription Processing API is running"
  }
  ```

#### 2. **System Status**
- **URL**: `GET /status`
- **Description**: Get detailed system status
- **Response**:
  ```json
  {
    "status": "operational",
    "version": "1.0.0",
    "models_available": {
      "ocr": true,
      "ner": true,
      "correction": true,
      "validation": true,
      "interaction": true
    },
    "description": "Prescription Processing System with 5 ML models"
  }
  ```

### Processing Endpoints

#### 3. **Process Prescription from Text**
- **URL**: `POST /process/text`
- **Description**: Process prescription text and extract medicines, validate, and check interactions
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "prescription_text": "Take Aspirin 500mg twice daily for 7 days. Metformin 1000mg once daily for 30 days.",
    "enable_ocr": false
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "medicines": [
      {
        "name": "Aspirin",
        "dosage": "500mg",
        "frequency": "twice daily",
        "duration": "7 days",
        "confidence": 0.95
      },
      {
        "name": "Metformin",
        "dosage": "1000mg",
        "frequency": "once daily",
        "duration": "30 days",
        "confidence": 0.92
      }
    ],
    "interactions": [
      {
        "drug1": "Aspirin",
        "drug2": "Metformin",
        "severity": "low",
        "risk_score": 0.50,
        "description": "Minor interaction - Monitor blood glucose levels"
      }
    ],
    "total_medicines": 2,
    "total_interactions": 1,
    "warnings": [],
    "processing_time_ms": 234.5
  }
  ```

#### 4. **Process Prescription from Image**
- **URL**: `POST /process/image`
- **Description**: Upload prescription image and get analysis
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file` (required): Image file (JPEG, PNG, BMP, TIFF)
- **Example with cURL**:
  ```bash
  curl -X POST "http://localhost:8000/process/image" \
    -F "file=@prescription.jpg"
  ```
- **Response**: Same as text processing

#### 5. **Batch Process Prescriptions**
- **URL**: `POST /process/batch`
- **Description**: Process multiple prescriptions in batch
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "prescriptions": [
      "Take Aspirin 500mg twice daily for 7 days",
      "Metformin 1000mg once daily for 30 days",
      "Ibuprofen 400mg as needed for pain"
    ]
  }
  ```
- **Response**:
  ```json
  {
    "status": "completed",
    "total_processed": 3,
    "results": [
      {
        "index": 0,
        "status": "success",
        "medicines_count": 1,
        "interactions_count": 0
      },
      {
        "index": 1,
        "status": "success",
        "medicines_count": 1,
        "interactions_count": 0
      },
      {
        "index": 2,
        "status": "success",
        "medicines_count": 1,
        "interactions_count": 0
      }
    ]
  }
  ```

## API Documentation

### Interactive Docs

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`

You can test all endpoints directly in these interfaces!

## Usage Examples

### Python Client

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Example 1: Process text prescription
response = requests.post(
    f"{BASE_URL}/process/text",
    json={
        "prescription_text": "Take Aspirin 500mg twice daily for 7 days",
        "enable_ocr": False
    }
)
result = response.json()
print(json.dumps(result, indent=2))

# Example 2: Check system status
response = requests.get(f"{BASE_URL}/status")
status = response.json()
print(f"System Status: {status['status']}")
print(f"Available Models: {status['models_available']}")

# Example 3: Batch processing
response = requests.post(
    f"{BASE_URL}/process/batch",
    json={
        "prescriptions": [
            "Take Aspirin 500mg twice daily",
            "Metformin 1000mg once daily"
        ]
    }
)
result = response.json()
print(f"Processed: {result['total_processed']} prescriptions")

# Example 4: Process image
with open("prescription.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/process/image", files=files)
    result = response.json()
    print(json.dumps(result, indent=2))
```

### JavaScript/Node.js Client

```javascript
const API_URL = 'http://localhost:8000';

// Process text prescription
async function processPrescriptionText(text) {
  const response = await fetch(`${API_URL}/process/text`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prescription_text: text,
      enable_ocr: false
    })
  });
  return await response.json();
}

// Process image
async function processPrescriptionImage(imageFile) {
  const formData = new FormData();
  formData.append('file', imageFile);
  
  const response = await fetch(`${API_URL}/process/image`, {
    method: 'POST',
    body: formData
  });
  return await response.json();
}

// Get system status
async function getSystemStatus() {
  const response = await fetch(`${API_URL}/status`);
  return await response.json();
}

// Usage
(async () => {
  const result = await processPrescriptionText(
    'Take Aspirin 500mg twice daily for 7 days'
  );
  console.log(result);
})();
```

### cURL Examples

```bash
# Process text prescription
curl -X POST "http://localhost:8000/process/text" \
  -H "Content-Type: application/json" \
  -d '{
    "prescription_text": "Take Aspirin 500mg twice daily for 7 days",
    "enable_ocr": false
  }'

# Get system status
curl -X GET "http://localhost:8000/status"

# Health check
curl -X GET "http://localhost:8000/health"

# Process image
curl -X POST "http://localhost:8000/process/image" \
  -F "file=@prescription.jpg"

# Batch processing
curl -X POST "http://localhost:8000/process/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "prescriptions": [
      "Take Aspirin 500mg twice daily",
      "Metformin 1000mg once daily"
    ]
  }'
```

## Response Models

### MedicineInfo
```json
{
  "name": "string (required)",
  "dosage": "string (optional)",
  "frequency": "string (optional)",
  "duration": "string (optional)",
  "confidence": "number (optional)"
}
```

### InteractionInfo
```json
{
  "drug1": "string (required)",
  "drug2": "string (required)",
  "severity": "string (required)",
  "risk_score": "number (required)",
  "description": "string (optional)"
}
```

### PrescriptionResponse
```json
{
  "status": "string (success/error)",
  "medicines": ["MedicineInfo[]"],
  "interactions": ["InteractionInfo[]"],
  "total_medicines": "integer",
  "total_interactions": "integer",
  "warnings": ["string[]"],
  "processing_time_ms": "number (optional)"
}
```

## Features

✅ **RESTful API** - Standard HTTP methods (GET, POST)
✅ **Data Validation** - Pydantic models for request/response validation
✅ **CORS Support** - Enabled for cross-origin requests
✅ **Interactive Docs** - Swagger UI and ReDoc
✅ **Error Handling** - Comprehensive error responses
✅ **Logging** - Detailed logging for debugging
✅ **Batch Processing** - Process multiple prescriptions
✅ **Image Support** - Direct image file uploads
✅ **Health Checks** - Built-in health monitoring
✅ **OpenAPI Schema** - Auto-generated API specification

## Configuration

### Server Configuration

Edit `main.py` to customize:

```python
uvicorn.run(
    app,
    host="0.0.0.0",      # Listen on all interfaces
    port=8000,           # Port number
    log_level="info",    # Logging level
    workers=4            # Number of workers (for production)
)
```

### CORS Configuration

The API allows all origins by default. Restrict in production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Deployment

### Development
```bash
uvicorn main:app --reload
```

### Production
```bash
# Using Gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# Or direct uvicorn with multiple workers
uvicorn main:app --host 0.0.0.0 --port 80 --workers 4
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t prescription-api .
docker run -p 8000:8000 prescription-api
```

## Performance Tips

1. **Model Caching**: Models are loaded once at startup
2. **Batch Processing**: Use batch endpoint for multiple prescriptions
3. **Image Optimization**: Reduce image file sizes before upload
4. **Workers**: Use multiple workers in production
5. **Async Processing**: API is async-ready for high concurrency

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Error processing prescription: Invalid input"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Security Considerations

- ✅ Input validation on all endpoints
- ✅ File type validation for image uploads
- ✅ Error messages don't expose sensitive info
- ⚠️ Enable authentication in production
- ⚠️ Use HTTPS for production deployments
- ⚠️ Rate limiting recommended for public APIs

## Troubleshooting

### Port Already in Use
```bash
# Change port
uvicorn main:app --port 8001
```

### Models Not Loading
```bash
# Check logs
python main.py  # View initialization errors
```

### CORS Issues
```bash
# Check CORS configuration in main.py
# Ensure client sends proper Origin header
```

## Next Steps

1. Run the API server
2. Visit `http://localhost:8000/api/docs`
3. Test endpoints interactively
4. Integrate with your application
5. Deploy to production

---

**API Version**: 1.0.0
**Framework**: FastAPI 0.104.1
**Server**: Uvicorn 0.24.0
