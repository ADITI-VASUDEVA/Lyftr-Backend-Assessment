from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
)

metadata = MetaData()

messages = Table(
    "messages",
    metadata,
    Column("message_id", String, primary_key=True),
    Column("from_msisdn", String, nullable=False),
    Column("to_msisdn", String, nullable=False),
    Column("ts", String, nullable=False),         
    Column("text", String),
    Column("created_at", String, nullable=False), 
)
