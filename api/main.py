from fastapi import Depends, FastAPI
from prometheus_client import Counter, generate_latest
from fastapi.responses import PlainTextResponse
import redis
from confluent_kafka import Producer
from sqlalchemy.orm import Session
from api.database import get_db, engine
from api.models import Event, Base, User
from sqlalchemy_utils import database_exists, create_database
from contextlib import asynccontextmanager
from pydantic import BaseModel


# Configuração Redis
redis_client = redis.Redis(host="redis", port=6379, db=0)


# Configuração Kafka
producer = Producer({"bootstrap.servers": "kafka:9092"})

# Contadores de exemplo (você pode criar mais para o Redis e outras operações)
REQUEST_COUNT = Counter("app_request_count", "Total number of requests")
# Contadores Prometheus
CACHE_HIT_COUNTER = Counter("redis_cache_hits", "Cache hit count for Redis")
CACHE_MISS_COUNTER = Counter("redis_cache_misses", "Cache miss count for Redis")


def init_db():
    print("Iniciando DB...")
    if not database_exists(engine.url):
        print("DB Não existe, criando")
        create_database(engine.url)  # Cria o banco de dados se ele não existir
    Base.metadata.create_all(bind=engine)  # Cria as tabelas
    print("DB Inicializado criando as tabelas")


# Definir o lifespan da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código para rodar no startup
    init_db()
    yield
    # Código para rodar no shutdown (se necessário)


app = FastAPI(lifespan=lifespan)


def serialize_event(event):
    return {
        "event_id": event.event_id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "event_data": event.event_data,
        "timestamp": event.timestamp,
    }


@app.get("/")
def read_root():
    REQUEST_COUNT.inc()  # Incrementa o contador a cada request
    return {"message": "LiveFeed Backend is running"}


# Expor as métricas no endpoint "/metrics"
@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return generate_latest()


# Modelo para criação de usuários
class UserCreate(BaseModel):
    username: str


@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(username=user.username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"user_id": new_user.user_id}


class EventCreate(BaseModel):
    user_id: int
    event_type: str
    event_data: dict


@app.post("/events/")
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    # 1. Criar o evento no PostgreSQL
    new_event = Event(
        user_id=event.user_id, event_type=event.event_type, event_data=event.event_data
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # 2. Cachear o evento no Redis
    redis_key = f"event_{new_event.event_id}"
    redis_client.set(redis_key, str(new_event), ex=60 * 10)  # Cache de 10 minutos

    # 3. Enviar o evento ao Kafka
    producer.produce("events_topic", key=str(new_event.event_id), value=str(new_event))
    producer.flush()

    return {"event_id": new_event.event_id}


@app.get("/feed/")
def get_feed(user_id: int, db: Session = Depends(get_db)):
    # 1. Tentar buscar o feed no Redis
    redis_key = f"user_feed_{user_id}"
    cached_feed = redis_client.get(redis_key)

    if cached_feed:
        # Incrementa o contador de hits no Redis
        CACHE_HIT_COUNTER.inc()
        return cached_feed
    else:
        # Incrementa o contador de misses no Redis
        CACHE_MISS_COUNTER.inc()
    # 2. Se não estiver no cache, buscar no PostgreSQL
    events = (
        db.query(Event)
        .filter_by(user_id=user_id)
        .order_by(Event.timestamp.desc())
        .limit(20)
        .all()
    )

    serialized_events = [serialize_event(event) for event in events]
    # 3. Armazenar o feed no Redis para futuras consultas
    redis_client.set(redis_key, str(serialized_events), ex=60 * 5)
    return serialized_events
