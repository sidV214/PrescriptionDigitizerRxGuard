# FastAPI Quick Start Guide

## 🚀 Get Started in 2 Minutes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the API Server
```bash
python run_api.py
```

Or alternatively:
```bash
uvicorn main:app --reload
```

You should see:
```
✓ API Running at: http://localhost:8000
📚 Swagger Docs: http://localhost:8000/api/docs
📖 ReDoc: http://localhost:8000/api/redoc
```

### Step 3: Test the API

#### Option A: Interactive Docs (Recommended)
Open browser and go to: **http://localhost:8000/api/docs**

You can test all endpoints directly!

#### Option B: Using Python
```python
import requests

# Process prescription text
response = requests.post(
    "http://localhost:8000/process/text",
    json={
        "prescription_text": "Take Aspirin 500mg twice daily for 7 days"
    }
)

print(response.json())
```

#### Option C: Using cURL
```bash
curl -X POST "http://localhost:8000/process/text" \
  -H "Content-Type: application/json" \
  -d '{"prescription_text": "Take Aspirin 500mg twice daily for 7 days"}'
```

## 📚 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/status` | GET | System status |
| `/process/text` | POST | Process text prescription |
| `/process/image` | POST | Process prescription image |
| `/process/batch` | POST | Process multiple prescriptions |

## 🔧 File Structure

```
s:\Ml-Models\
├── main.py                ← FastAPI application
├── run_api.py            ← Quick start script
├── api_client_examples.py ← Client examples
├── API_DOCUMENTATION.md   ← Full documentation
├── requirements.txt       ← Dependencies (updated)
├── pipeline.py           ← Existing ML pipeline
└── models/              ← Existing ML models
```

## 📝 Common Tasks

### Process Prescription from Text
```python
import requests

response = requests.post("http://localhost:8000/process/text", json={
    "prescription_text": "Aspirin 500mg twice daily for 7 days. Metformin 1000mg once daily.",
})
result = response.json()
print(f"Medicines: {result['total_medicines']}")
print(f"Interactions: {result['total_interactions']}")
```

### Process Prescription Image
```python
response = requests.post(
    "http://localhost:8000/process/image",
    files={"file": open("prescription.jpg", "rb")}
)
result = response.json()
```

### Batch Processing
```python
response = requests.post("http://localhost:8000/process/batch", json={
    "prescriptions": [
        "Aspirin 500mg twice daily",
        "Metformin 1000mg once daily",
        "Ibuprofen 400mg as needed"
    ]
})
result = response.json()
```

### Check System Status
```python
response = requests.get("http://localhost:8000/status")
status = response.json()
print(f"Status: {status['status']}")
print(f"Models: {status['models_available']}")
```

## 🧪 Run Examples

```bash
# Run all example scenarios
python api_client_examples.py
```

This will demonstrate:
- Health checks
- Text processing
- Batch processing
- Image processing
- Error handling
- Advanced usage

## 🌐 Access Points

- **API Endpoint**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/api/docs (for testing)
- **ReDoc**: http://localhost:8000/api/redoc (for docs)
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json

## ⚙️ Configuration

### Change Port
```bash
uvicorn main:app --port 8001
```

### Production Mode (No reload)
```bash
uvicorn main:app
```

### Multiple Workers (Production)
```bash
python -m gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## 🔗 Integration Examples

### JavaScript/React
```javascript
const response = await fetch('http://localhost:8000/process/text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    prescription_text: 'Aspirin 500mg twice daily'
  })
});
const result = await response.json();
console.log(result);
```

### Python Flask Integration
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
API_URL = 'http://localhost:8000'

@app.route('/analyze', methods=['POST'])
def analyze_prescription():
    data = request.json
    response = requests.post(f'{API_URL}/process/text', json=data)
    return response.json()
```

### Docker Deployment
```bash
# Build image
docker build -t prescription-api .

# Run container
docker run -p 8000:8000 prescription-api
```

## 🆘 Troubleshooting

**Port 8000 already in use?**
```bash
# Use a different port
uvicorn main:app --port 8001
```

**API won't start?**
```bash
# Check dependencies
pip install -r requirements.txt

# Check for errors
python main.py
```

**Models not loading?**
```bash
# Verify models are installed
python -m spacy download en_core_web_sm

# Check log output
python run_api.py  # Shows detailed logs
```

## 📖 Next Steps

1. ✅ Server running
2. 📖 Read [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for full details
3. 🧪 Run [api_client_examples.py](api_client_examples.py)
4. 🔗 Integrate with your application
5. 🚀 Deploy to production

## 💡 Tips

- Use Swagger UI (`/api/docs`) to test endpoints interactively
- Check `processing_time_ms` in responses for performance monitoring
- Use batch endpoint for processing multiple prescriptions
- All responses include detailed warnings and error information
- API logs show detailed processing information (run with `--reload` for dev)

---

**Ready?** Start with: `python run_api.py` 🚀
