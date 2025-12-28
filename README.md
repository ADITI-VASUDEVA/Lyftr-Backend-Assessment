# Lyftr AI – Backend Assignment  
Containerized Webhook API

## Overview

This project implements a production-style backend service using **FastAPI** and **SQLite** that ingests WhatsApp-like webhook messages exactly once, exposes query and analytics APIs, and provides basic observability via health checks, structured logs, and metrics.

The service is containerized using Docker and runs locally via Docker Compose.

---

## Tech Stack

- Python 3.11
- FastAPI
- SQLite (file-backed, via SQLAlchemy Core)
- Docker & Docker Compose

---

## How to Run

### Prerequisites
- Docker + Docker Compose installed
- `make` available (or run Docker commands directly)

### Start the service
```bash
export WEBHOOK_SECRET="testsecret"
make up
```


The API will be available at: http://localhost:8000

## Stop & clean up
 ```bash
 make down
```

## View logs
```bash
  make logs
```
 ### Health Checks

  1. Liveness
     ```bash
    curl http://localhost:8000/health/live
  ``
    Always returns 200 once the process is running.

  2. Readiness

    curl http://localhost:8000/health/ready
``
    Returns 200 only if:
    1. Database is reachable and schema initialized
    2. WEBHOOK_SECRET is set
       Otherwise returns 503.

## Webhook Ingestion

 ###  Endpoint -> POST /webhook

 ### Headers
  1. Content-Type: application/json
  2. X-Signature: hex-encoded HMAC-SHA256 of the raw request body, using WEBHOOK_SECRET

 Request Body :
 ```bash
 {
  "message_id": "m1",
  "from": "+919876543210",
  "to": "+14155550100",
  "ts": "2025-01-15T10:00:00Z",
  "text": "Hello"
 }
```
 ### Behavior

 1. Invalid or missing signature → 401 (no DB insert)
 2. Invalid payload → 422
 3. First valid request for a message_id → stored, 200
 4. Subsequent valid requests with same message_id → idempotent 200

Success Response :
```bash
{ "status": "ok" }
```
## Listing Messages

###  Endpoint -> GET /messages

### Query Parameters

 1. limit (default 50, max 100)
 2. offset (default 0)
 3. from – filter by sender
 4. since – ISO-8601 UTC timestamp
 5. q – case-insensitive substring search in message text

##  Ordering

 Messages are always ordered by:

 ts ASC, message_id ASC

 Response :
 ```bash
{
  "data": [...],
  "total": 4,
  "limit": 2,
  "offset": 0
}
```
##  Analytics

### Endpoint -> GET /stats

  Response:
  ```bash
 {
  "total_messages": 123,
  "senders_count": 10,
  "messages_per_sender": [
    {"from": "+919876543210", "count": 50 }
  ],
  "first_message_ts": "2025-01-10T09:00:00Z",
  "last_message_ts": "2025-01-15T10:00:00Z"
 }
```
 If no messages exist, timestamps are returned as null.


## Metrics

### Endpoint -> GET /metrics

 Exposes Prometheus-style metrics including:
 1. http_requests_total{path,status}
 2. webhook_requests_total{result}

This endpoint always returns 200 and plain text output.

## Logging

 Each request emits a single structured JSON log line including:

 1. timestamp
 2. request_id
 3. method
 4. path
 5. status
 6. latency_ms

 For /webhook requests, logs also include:

 1. message_id
 2. dup
 3. result

This format is compatible with tools like jq and log aggregators.

## Design Decisions

 ### HMAC Verification

 The webhook signature is computed using the raw request body bytes, not parsed JSON, to avoid serialization mismatches. Signature comparison uses constant-time checks.

 ### Idempotency

 Exactly-once semantics are enforced via a database-level primary key on message_id, with graceful handling of duplicate inserts.

 ### Pagination Contract

 Total always reflects the number of records matching the filters before applying limit and offset.

 ### Database Access

 SQLAlchemy Core (not ORM) is used purely as a SQL execution layer over SQLite for clarity, safety, and explicit control.

## Setup Used

 1. VS Code
 2. Docker Desktop
 3. Occasional use of AI tools (Copilot,ChatGPT) for reasoning and validation


## Author:
Aditi Vasudeva

Backend Assignment Submission
