from fastapi import FastAPI, Body, Response
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from lxml import etree
from pathlib import Path
import json
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter

ANALYTICS_COUNTER = Counter("analytics_records_total", "Total analytics records received")

app = FastAPI(title="Mock APIs", version="1.0.0")

# Data directory and helpers
DATA_DIR = Path(__file__).resolve().parent / "data"
CUSTOMERS_FILE = DATA_DIR / "customers.json"
PRODUCTS_FILE = DATA_DIR / "products.json"

def _load_json(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Customer(BaseModel):
    id: str
    email: str
    name: str
    status: str = Field(default="active")
    updated_at: Optional[str] = None

class Product(BaseModel):
    product_id: str
    sku: str
    qty: int
    updated_at: Optional[str] = None

@app.get("/customers", response_model=List[Customer], summary="GET /customers")
async def get_customers():
    return _load_json(CUSTOMERS_FILE)

@app.post("/customers", response_model=Customer, summary="POST /customers")
async def add_customer(customer: Customer):
    customers = _load_json(CUSTOMERS_FILE)
    c = customer.model_dump()
    c["updated_at"] = c.get("updated_at") or datetime.utcnow().isoformat() + "Z"
    customers.append(c)
    _save_json(CUSTOMERS_FILE, customers)
    return c

@app.get("/products", response_model=List[Product], summary="GET /products")
async def get_products():
    return _load_json(PRODUCTS_FILE)

# SOAP-like endpoint stub for AddCustomer
@app.post("/soap/AddCustomer", summary="SOAP AddCustomer stub", response_class=Response)
async def soap_add_customer(payload: str = Body(..., media_type="text/xml")):
    # Very light XML parse to extract name/email (if present) and return a mock SOAP envelope
    try:
        root = etree.fromstring(payload.encode("utf-8"))
        nsmap = root.nsmap
        # naive search for elements
        email_el = root.find('.//email', namespaces=nsmap) or root.find('.//Email', namespaces=nsmap)
        name_el = root.find('.//name', namespaces=nsmap) or root.find('.//Name', namespaces=nsmap)
        email = email_el.text if email_el is not None else "unknown@example.com"
        name = name_el.text if name_el is not None else "Unknown"
        customers = _load_json(CUSTOMERS_FILE)
        new_id = f"c{len(customers)+1}"
        customers.append({"id": new_id, "email": email, "name": name, "status": "active", "updated_at": datetime.utcnow().isoformat() + "Z"})
        _save_json(CUSTOMERS_FILE, customers)
        response_xml = f"""
<soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'>
  <soap:Body>
    <AddCustomerResponse>
      <status>SUCCESS</status>
      <customerId>{new_id}</customerId>
    </AddCustomerResponse>
  </soap:Body>
</soap:Envelope>"""
        return Response(content=response_xml, media_type="text/xml")
    except Exception:
        fault_xml = """
<soap:Envelope xmlns:soap='http://schemas.xmlsoap.org/soap/envelope/'>
  <soap:Body>
    <soap:Fault>
      <faultcode>soap:Server</faultcode>
      <faultstring>Invalid SOAP request</faultstring>
    </soap:Fault>
  </soap:Body>
</soap:Envelope>"""
        return Response(content=fault_xml, media_type="text/xml", status_code=400)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.post("/analytics/data")
async def analytics_data(payload: Any = Body(...)):
    # Accept either a dict or list of dicts
    count = 1
    if isinstance(payload, list):
        count = len(payload)
    ANALYTICS_COUNTER.inc(count)
    return {"status": "ok", "received": count}

# CSV upload endpoint for analytics
@app.post("/analytics/upload", summary="Upload analytics data as CSV", response_model=dict)
async def analytics_upload(csv_body: str = Body(..., media_type="text/csv")):
    # Count non-empty data rows (assume header present if first line contains non-numeric ids)
    lines = [ln for ln in csv_body.splitlines() if ln.strip()]
    count = 0
    if lines:
        # naive header detection: if any of the first line cells contain letters, treat as header
        header = lines[0]
        data_lines = lines[1:] if any(ch.isalpha() for ch in header) else lines
        count = len(data_lines)
    ANALYTICS_COUNTER.inc(count)
    return {"status": "ok", "received": count}
