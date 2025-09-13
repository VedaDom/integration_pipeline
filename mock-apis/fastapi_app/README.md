# Mock APIs (FastAPI)

Endpoints:
- GET /customers
- POST /customers
- GET /products
- POST /soap/AddCustomer (SOAP-like XML stub)

Run locally:
```
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

OpenAPI docs: http://localhost:8000/docs
