# Integration Guide: Research Agent and Financial Analysis Agent

## Summary

Two new agents have been added to the Sovereign Sentinel system:

1. **Research Agent**: Extracts financial data from Xero, QuickBooks, and Stripe using Composio MCP
2. **Financial Analysis Agent**: Analyzes loans using rules and risk-based heuristics

## Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Composio API Key (get from https://composio.dev)
COMPOSIO_API_KEY=your_composio_api_key_here
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## New API Endpoints

### 1. Extract Financial Data

**POST** `/api/research/extract`

Extracts loan data from an external source.

**Body (JSON):**
```json
{
  "source": "xero",  // "xero" | "quickbooks" | "stripe"
  "connection_id": "conn_123",
  "tenant_id": "tenant_456"  // Required for Xero and QuickBooks
}
```

**Response:**
```json
{
  "source": "xero",
  "loans": [
    {
      "loanId": "XERO_123_456",
      "borrower": "Acme Corp",
      "industry": "energy",
      "interestType": "PIK",
      "principalAmount": 10000000,
      "outstandingBalance": 12500000,
      "maturityDate": "2025-12-31T00:00:00Z",
      "covenants": []
    }
  ],
  "count": 1,
  "status": "success"
}
```

### 2. Analyze Portfolio

**POST** `/api/analysis/analyze`

Analyzes a loan portfolio using Financial Analysis Agent or traditional method.

**Body (JSON):**
```json
{
  "loans": [
    {
      "loanId": "L001",
      "borrower": "Acme Energy",
      "industry": "energy",
      "interestType": "PIK",
      "principalAmount": 10000000,
      "outstandingBalance": 12500000,
      "maturityDate": "2025-12-31T00:00:00Z",
      "covenants": []
    }
  ],
  "use_ai": true  // true = uses Financial Analysis Agent, false = uses traditional Forensic Auditor
}
```

**Response:**
```json
{
  "total_loans": 1,
  "flagged_count": 1,
  "analysis_method": "ai",
  "flagged_loans": [
    {
      "loanId": "L001",
      "borrower": "Acme Energy",
      "risk_level": "critical",
      "flag_reason": "PIK loan in high-risk sector",
      "correlated_event": "Current geopolitical events",
      "flagged_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 3. Extract and Analyze (Combined)

**POST** `/api/research/analyze-and-extract`

Extracts data and analyzes it in a single step.

**Body (JSON):**
```json
{
  "source": "quickbooks",
  "connection_id": "conn_123",
  "tenant_id": "company_456",
  "use_ai": true
}
```

**Response:**
```json
{
  "source": "quickbooks",
  "extracted_count": 5,
  "flagged_count": 2,
  "analysis_method": "ai",
  "flagged_loans": [...]
}
```

## Recommended Workflow

### Option 1: Separate Extraction and Analysis

```python
import requests

# 1. Extract data
response = requests.post(
    "http://localhost:8000/api/research/extract",
    json={
        "source": "xero",
        "connection_id": "your_connection_id",
        "tenant_id": "your_tenant_id"
    }
)
loans_data = response.json()["loans"]

# 2. Analyze
analysis_response = requests.post(
    "http://localhost:8000/api/analysis/analyze",
    json={
        "loans": loans_data,
        "use_ai": True
    }
)
flagged = analysis_response.json()["flagged_loans"]
```

### Option 2: All in One

```python
import requests

response = requests.post(
    "http://localhost:8000/api/research/analyze-and-extract",
    json={
        "source": "quickbooks",
        "connection_id": "your_connection_id",
        "tenant_id": "your_company_id",
        "use_ai": True
    }
)
results = response.json()
```

## Composio Configuration

### 1. Get API Key

1. Sign up at https://composio.dev
2. Get API key from dashboard
3. Add to `.env`: `COMPOSIO_API_KEY=your_key`

### 2. Connect Applications

To connect Xero, QuickBooks, or Stripe:

1. Use Composio SDK to create OAuth connections
2. Or use Composio dashboard to connect manually
3. Get `connection_id` after connecting

**Connection example (using Composio SDK):**
```python
from composio import ComposioClient

client = ComposioClient(api_key="your_key")
connection = client.connect_app(
    app="xero",
    entity_id="your_entity_id"
)
connection_id = connection.id
```

## Troubleshooting

### Error: "Research Agent not initialized"
- Verify that `COMPOSIO_API_KEY` is in `.env`
- Restart server after adding the variable

### Error: "Composio is not installed"
```bash
pip install composio-core
```

### Error: "Financial Analysis Agent not initialized"
- Check server logs for specific error
- Agent should initialize automatically on server start

## Notes

- Research Agent requires active OAuth connections for each source
- Financial Analysis Agent uses rule-based analysis and heuristics
- Analysis is fast and doesn't require external models
- Agent considers multiple factors: interest type, balance, global risk, affected sectors
