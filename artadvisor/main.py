# main.py — ArtAdvisor API (O Garçom)
# FastAPI server com banco de dados SQLAlchemy.
# Serve o feed diário de obras e aprende o gosto via likes.

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import date
from pydantic import BaseModel
import os

# ──────────────────────────────────────────────────────────
# 1. CONFIGURAÇÃO DO BANCO DE DADOS
# ──────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./artadvisor.db")

# Railway usa postgres://, mas SQLAlchemy precisa de postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ──────────────────────────────────────────────────────────
# 2. MODELOS DO BANCO (AS TABELAS)
# ──────────────────────────────────────────────────────────
class Obra(Base):
    """Uma obra de arte curada pela IA."""
    __tablename__ = "obras"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    imagem_url = Column(String, nullable=False)
    tags_extraidas = Column(String, default="")  # ex: "impasto, abstrato, azul"
    data_exibicao = Column(Date, default=date.today)
    curtiu = Column(Boolean, default=False)


class PerfilGosto(Base):
    """
    Memória do gosto artístico.
    Cada tag tem um peso — quanto mais curtida, maior o peso.
    """
    __tablename__ = "perfil_gosto"

    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, unique=True, nullable=False)
    peso = Column(Integer, default=1)


# Cria as tabelas fisicamente no banco
Base.metadata.create_all(bind=engine)


# ──────────────────────────────────────────────────────────
# 3. SERVIDOR FASTAPI
# ──────────────────────────────────────────────────────────
app = FastAPI(
    title="ArtAdvisor API",
    description="Curadoria de arte personalizada com IA 🎨",
    version="1.0.0",
)

# Permite o iPhone se conectar (CORS aberto para dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Dependency injection: abre e fecha sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────────────────────
# 4. SCHEMAS DE RESPOSTA (Pydantic)
# ──────────────────────────────────────────────────────────
class ObraResponse(BaseModel):
    id: int
    titulo: str
    imagem_url: str
    tags_extraidas: str
    curtiu: bool

    class Config:
        from_attributes = True


class LikeResponse(BaseModel):
    status: str
    curtiu: bool


class PerfilResponse(BaseModel):
    tag: str
    peso: int

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────
# 5. ROTAS — O QUE O IPHONE VAI CHAMAR
# ──────────────────────────────────────────────────────────

@app.get("/")
def raiz():
    """Health check — confirma que a API está no ar."""
    return {"status": "online", "mensagem": "ArtAdvisor API 🎨 está funcionando!"}


@app.get("/feed/hoje", response_model=list[ObraResponse])
def obter_feed_do_dia(db: Session = Depends(get_db)):
    """
    O iPhone chama esta rota ao abrir o app.
    Retorna todas as obras curadas para hoje.
    """
    return db.query(Obra).filter(Obra.data_exibicao == date.today()).all()


@app.post("/obra/{obra_id}/like", response_model=LikeResponse)
def dar_like(obra_id: int, db: Session = Depends(get_db)):
    """
    O iPhone avisa do ❤️ e a IA aprende!
    Toggle: se já curtiu, descurte. Se não curtiu, curte.
    Ao curtir, aumenta o peso das tags associadas à obra.
    """
    obra = db.query(Obra).filter(Obra.id == obra_id).first()
    if not obra:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    # Toggle do like
    obra.curtiu = not obra.curtiu

    # APRENDIZADO: aumenta o peso das tags quando curte
    if obra.curtiu and obra.tags_extraidas:
        tags = [t.strip().lower() for t in obra.tags_extraidas.split(",")]
        for tag_nome in tags:
            if not tag_nome:
                continue
            perfil = db.query(PerfilGosto).filter(PerfilGosto.tag == tag_nome).first()
            if perfil:
                perfil.peso += 1
            else:
                db.add(PerfilGosto(tag=tag_nome, peso=1))

    db.commit()
    db.refresh(obra)
    return LikeResponse(status="sucesso", curtiu=obra.curtiu)


@app.get("/perfil", response_model=list[PerfilResponse])
def ver_perfil_gosto(db: Session = Depends(get_db)):
    """Rota auxiliar: mostra o perfil de gosto aprendido."""
    return db.query(PerfilGosto).order_by(PerfilGosto.peso.desc()).all()


# ──────────────────────────────────────────────────────────
# 6. AGENDADOR — CURADORIA AUTOMÁTICA ÀS 04:00 AM
# ──────────────────────────────────────────────────────────
import schedule
import threading
import time


def _rodar_curadoria_segura():
    """Wrapper que importa e roda o curador com tratamento de erro."""
    try:
        from curador import rodar_curadoria
        rodar_curadoria()
    except Exception as e:
        print(f"❌ Erro no agendador: {e}")


# Agenda a curadoria diária às 04:00 AM
schedule.every().day.at("04:00").do(_rodar_curadoria_segura)


def _loop_agendador():
    """Loop infinito que verifica tarefas agendadas a cada 60s."""
    print("⏰ Agendador iniciado — curadoria programada para 04:00 AM")
    while True:
        schedule.run_pending()
        time.sleep(60)


# Inicia o agendador em uma thread daemon (morre junto com o servidor)
threading.Thread(target=_loop_agendador, daemon=True).start()


@app.post("/rodar-curadoria")
def disparar_curadoria_manual():
    """Rota para disparar a curadoria manualmente (útil para testes)."""
    threading.Thread(target=_rodar_curadoria_segura, daemon=True).start()
    return {"status": "Curadoria iniciada em background! 🎨"}

