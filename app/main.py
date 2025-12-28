from fastapi import FastAPI, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import load_settings
from app.storage import create_db_engine, init_db
from fastapi import Request, HTTPException
from app.schemas import WebhookMessage
from app.security import verify_signature
from app.storage import insert_message
from app.logging_utils import setup_logger, new_request_id, now_iso
from app.metrics import http_requests_total, webhook_requests_total, Timer
from fastapi import Query
from app.storage import fetch_messages
from app.storage import compute_stats

from fastapi.responses import PlainTextResponse
from app.metrics import render_metrics




settings = load_settings()
engine = create_db_engine(settings.database_url)

app = FastAPI(title="Lyftr AI Backend Assignment")


@app.on_event("startup")
def startup() -> None:
    
    init_db(engine)


@app.get("/health/live")
def health_live():
    return {"status": "live"}


@app.get("/health/ready")
def health_ready(response: Response):
    
    if not settings.webhook_secret:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready"}

    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready"}

    return {"status": "ready"}


logger = setup_logger(settings.log_level)


@app.post("/webhook")
async def webhook(request: Request):
    request_id = new_request_id()
    raw_body = await request.body()
    signature = request.headers.get("X-Signature")

    with Timer() as timer:
        
        if not settings.webhook_secret or not verify_signature(
            settings.webhook_secret, raw_body, signature
        ):
            webhook_requests_total["invalid_signature"] += 1
            http_requests_total[("/webhook", 401)] += 1

            logger.info({
                "ts": now_iso(),
                "level": "ERROR",
                "request_id": request_id,
                "method": "POST",
                "path": "/webhook",
                "status": 401,
                "latency_ms": timer.ms,
                "result": "invalid_signature",
            })

            raise HTTPException(status_code=401, detail="invalid signature")

        
        msg = WebhookMessage.model_validate_json(raw_body)

        
        result = insert_message(engine, msg.model_dump())

        webhook_requests_total[result] += 1
        http_requests_total[("/webhook", 200)] += 1

        logger.info({
            "ts": now_iso(),
            "level": "INFO",
            "request_id": request_id,
            "method": "POST",
            "path": "/webhook",
            "status": 200,
            "latency_ms": timer.ms,
            "message_id": msg.message_id,
            "dup": result == "duplicate",
            "result": result,
        })

        return {"status": "ok"}
 
@app.get("/messages")
def list_messages(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    from_: str | None = Query(None, alias="from"),
    since: str | None = None,
    q: str | None = None,
):
    total, rows = fetch_messages(
        engine,
        limit=limit,
        offset=offset,
        from_msisdn=from_,
        since=since,
        q=q,
    )

    data = [
        {
            "message_id": row["message_id"],
            "from": row["from_msisdn"],
            "to": row["to_msisdn"],
            "ts": row["ts"],
            "text": row["text"],
        }
        for row in rows
    ]

    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
   
@app.get("/stats")
def stats():
    return compute_stats(engine)

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return render_metrics()
