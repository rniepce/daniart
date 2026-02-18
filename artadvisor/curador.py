# curador.py — Robô Curador (O Chef da Madrugada)
# Roda como agendamento automático às 04:00 AM.
# FOCO: Arte contemporânea de artistas atuais e independentes.
# 1. Lê o perfil de gosto (o que ela tem curtido).
# 2. Pede ao GPT um termo de busca contemporâneo.
# 3. Busca obras pós-1950 na API do Art Institute of Chicago.
# 4. GPT traduz e cria tags em português.
# 5. Salva no banco para a API servir de manhã.

import os
import requests
import json
import random
from openai import OpenAI
from datetime import date

# Importa os modelos e sessão do banco a partir do main.py
from main import Obra, PerfilGosto, SessionLocal

# ──────────────────────────────────────────────
# CONFIGURAÇÃO
# ──────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-sua-chave-openai-aqui")
client = OpenAI(api_key=OPENAI_API_KEY)

# Art Institute of Chicago API (gratuita, sem chave!)
ARTIC_API_URL = "https://api.artic.edu/api/v1"
ARTIC_IIIF_URL = "https://www.artic.edu/iiif/2"

# Termos de busca para arte contemporânea / emergente
TERMOS_CONTEMPORANEOS = [
    "contemporary painting 2000s",
    "emerging artist mixed media",
    "contemporary abstract texture",
    "new figurative painting",
    "urban contemporary art",
    "contemporary sculpture installation",
    "digital age painting",
    "postmodern art 21st century",
    "contemporary collage assemblage",
    "neo-expressionism painting",
    "contemporary photography art",
    "street art influenced painting",
    "minimalist contemporary",
    "contemporary landscape reimagined",
    "identity contemporary art",
    "contemporary feminist art",
    "black contemporary artists",
    "latin american contemporary art",
    "asian contemporary painting",
    "contemporary portrait modern",
]


def buscar_obras_contemporaneas(termo: str, limite: int = 20) -> list[dict]:
    """
    Busca obras CONTEMPORÂNEAS no Art Institute of Chicago.
    Usa filtros para pegar obras pós-1950 com imagem.
    """
    print(f"🏛️ Buscando arte contemporânea: {termo}")

    # Busca com filtros via Elasticsearch query avançada (POST para garantir complexidade)
    url = f"{ARTIC_API_URL}/artworks/search"
    payload = {
        "q": termo,
        "fields": [
            "id", "title", "image_id", "artist_title", "date_end",
            "style_titles", "classification_titles", "term_titles", "department_title"
        ],
        "limit": limite,
        "query": {
            "bool": {
                "must": [
                    {"range": {"date_end": {"gte": 2020, "lte": 2030}}},
                    {"exists": {"field": "image_id"}},
                ],
            }
        },
    }

    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        print(f"❌ Erro na busca: {resp.text}")
        return []

    dados = resp.json()
    iiif_url = dados.get("config", {}).get("iiif_url", ARTIC_IIIF_URL)
    items = dados.get("data", [])

    obras = []
    for item in items:
        image_id = item.get("image_id")
        if not image_id:
            continue

        # Extrai metadados
        estilos = item.get("style_titles", []) or []
        termos = item.get("term_titles", []) or []
        classificacao = item.get("classification_titles", []) or []
        todas_tags = estilos + termos + classificacao
        ano = item.get("date_end", "?")
        depto = item.get("department_title", "")

        obras.append({
            "titulo_original": item.get("title", "Untitled"),
            "artista": item.get("artist_title", "Unknown"),
            "ano": ano,
            "departamento": depto,
            "image_id": image_id,
            "tags_api": todas_tags[:5],
        })

    print(f"✅ Encontradas {len(obras)} obras contemporâneas com imagem")
    return obras


def traduzir_e_taguear(obras: list[dict]) -> list[dict]:
    """
    Usa o GPT para traduzir títulos e criar tags em português.
    Foco em valorizar o artista contemporâneo e a técnica.
    """
    if not obras:
        return []

    print("🧠 Pedindo ao GPT para curar e traduzir...")

    lista_obras = []
    for i, obra in enumerate(obras):
        lista_obras.append({
            "index": i,
            "titulo": obra["titulo_original"],
            "artista": obra["artista"],
            "ano": obra["ano"],
            "tags_api": obra["tags_api"],
        })

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Você é um curador de arte contemporânea especializado em artistas "
                    "emergentes e independentes. Receba esta lista e selecione as 10 obras "
                    "mais interessantes e visualmente impactantes. Priorize obras de "
                    "artistas menos conhecidos e técnicas inovadoras.\n\n"
                    "Retorne um JSON com a chave 'obras' contendo um array. Para cada obra:\n"
                    "- 'index': índice original\n"
                    "- 'titulo': título poético traduzido para português\n"
                    "- 'artista': nome do artista original\n"
                    "- 'tags': 3 palavras-chave de estilo/técnica em português (separadas por vírgula)\n\n"
                    f"Obras: {json.dumps(lista_obras, ensure_ascii=False)}"
                ),
            }
        ],
    )

    resultado = json.loads(resposta.choices[0].message.content)
    obras_traduzidas = resultado.get("obras", [])
    print(f"🎨 GPT selecionou {len(obras_traduzidas)} obras contemporâneas")
    return obras_traduzidas


def rodar_curadoria():
    """Pipeline completo de curadoria diária — foco contemporâneo."""
    print("=" * 50)
    print("🤖 ROBÔ CURADOR — Curadoria Contemporânea")
    print("=" * 50)

    db = SessionLocal()

    try:
        # 1. Lê a memória: O que ela tem curtido mais?
        top_tags = (
            db.query(PerfilGosto)
            .order_by(PerfilGosto.peso.desc())
            .limit(3)
            .all()
        )
        gosto_str = (
            ", ".join([t.tag for t in top_tags])
            if top_tags
            else "contemporary abstract, mixed media, texture"
        )
        print(f"💭 Gostos atuais: {gosto_str}")

        # 2. Pede ao GPT um termo focado em arte contemporânea
        resp_termo = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Crie um termo de busca curto em inglês para encontrar "
                        f"ARTE CONTEMPORÂNEA de artistas atuais e independentes, "
                        f"focado nestes estilos: {gosto_str}. "
                        f"Inclua palavras como 'contemporary', 'modern', 'emerging'. "
                        f"Retorne APENAS o termo, sem aspas ou explicações."
                    ),
                }
            ],
        )
        termo_gpt = resp_termo.choices[0].message.content.strip().strip('"')

        # Também escolhe um termo aleatório da lista para variar
        termo_extra = random.choice(TERMOS_CONTEMPORANEOS)

        print(f"🔎 Termo GPT: {termo_gpt}")
        print(f"🔎 Termo extra: {termo_extra}")

        # 3. Busca com os dois termos e combina resultados
        obras_gpt = buscar_obras_contemporaneas(termo_gpt)
        obras_extra = buscar_obras_contemporaneas(termo_extra)

        # Combina e remove duplicatas por image_id
        vistas = set()
        todas_obras = []
        for obra in obras_gpt + obras_extra:
            if obra["image_id"] not in vistas:
                vistas.add(obra["image_id"])
                todas_obras.append(obra)

        if not todas_obras:
            print("⚠️ Nenhuma obra encontrada. Encerrando.")
            return

        print(f"📦 Total combinado (sem duplicatas): {len(todas_obras)} obras")

        # 4. GPT curates and translates
        obras_traduzidas = traduzir_e_taguear(todas_obras)

        # 5. Salva no Banco de Dados
        hoje = date.today()
        for obra_trad in obras_traduzidas:
            idx = obra_trad.get("index", 0)
            if idx < len(todas_obras):
                obra_original = todas_obras[idx]
                artista = obra_trad.get("artista", obra_original["artista"])
                titulo = obra_trad.get("titulo", "Sem título")

                nova_obra = Obra(
                    titulo=f"{titulo} — {artista}",
                    imagem_url=obra_original["image_id"],
                    tags_extraidas=obra_trad.get("tags", ""),
                    data_exibicao=hoje,
                )
                db.add(nova_obra)

        db.commit()
        count = len(obras_traduzidas)
        print(f"\n🎨 Curadoria concluída! {count} obras contemporâneas salvas.")

    except Exception as e:
        print(f"❌ Erro na curadoria: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    rodar_curadoria()
