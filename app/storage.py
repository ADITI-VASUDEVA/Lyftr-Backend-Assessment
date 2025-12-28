from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from app.models import metadata
from datetime import datetime, timezone
from sqlalchemy import insert, select, func, and_, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine

from app.models import messages


def create_db_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False},  
        future=True,
    )


def init_db(engine: Engine) -> None:
    try:
        metadata.create_all(engine)
    except SQLAlchemyError as exc:
        raise RuntimeError("Failed to initialize database") from exc



def insert_message(engine: Engine, msg: dict) -> str:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    stmt = insert(messages).values(
        message_id=msg["message_id"],
        from_msisdn=msg["from_msisdn"],
        to_msisdn=msg["to_msisdn"],
        ts=msg["ts"],
        text=msg.get("text"),
        created_at=now,
    )

    try:
        with engine.begin() as conn:
            conn.execute(stmt)
        return "created"
    except IntegrityError:
        # message_id already exists → idempotent duplicate
        return "duplicate"



def fetch_messages(
    engine: Engine,
    *,
    limit: int,
    offset: int,
    from_msisdn: str | None,
    since: str | None,
    q: str | None,
):
    conditions = []

    if from_msisdn:
        conditions.append(messages.c.from_msisdn == from_msisdn)

    if since:
        conditions.append(messages.c.ts >= since)

    if q:
        conditions.append(messages.c.text.ilike(f"%{q}%"))

    where_clause = and_(*conditions) if conditions else None

    
    count_stmt = select(func.count()).select_from(messages)
    if where_clause is not None:
        count_stmt = count_stmt.where(where_clause)

    
    data_stmt = (
        select(messages)
        .order_by(messages.c.ts.asc(), messages.c.message_id.asc())
        .limit(limit)
        .offset(offset)
    )

    if where_clause is not None:
        data_stmt = data_stmt.where(where_clause)

    with engine.connect() as conn:
        total = conn.execute(count_stmt).scalar_one()
        rows = conn.execute(data_stmt).mappings().all()

    return total, rows


def compute_stats(engine: Engine):
    with engine.connect() as conn:
        # total messages
        total_messages = conn.execute(
            select(func.count()).select_from(messages)
        ).scalar_one()

        # unique senders
        senders_count = conn.execute(
            select(func.count(func.distinct(messages.c.from_msisdn)))
        ).scalar_one()

        # messages per sender (top 10)
        per_sender_rows = conn.execute(
            select(
                messages.c.from_msisdn,
                func.count().label("count"),
            )
            .group_by(messages.c.from_msisdn)
            .order_by(desc("count"))
            .limit(10)
        ).all()

        # first & last timestamps
        first_ts, last_ts = conn.execute(
            select(
                func.min(messages.c.ts),
                func.max(messages.c.ts),
            )
        ).one()

    return {
        "total_messages": total_messages,
        "senders_count": senders_count,
        "messages_per_sender": [
            {"from": row.from_msisdn, "count": row.count}
            for row in per_sender_rows
        ],
        "first_message_ts": first_ts,
        "last_message_ts": last_ts,
    }
