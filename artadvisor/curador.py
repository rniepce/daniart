# curador.py — Robô Curador (O Chef da Madrugada)
# Roda como agendamento automático às 04:00 AM.
# 1. Lê o perfil de gosto (o que ela tem curtido).
# 2. Pede ao GPT um termo de busca em inglês.
# 3. Busca obras na API gratuita do Art Institute of Chicago.
# 4. GPT cria títulos em português e extrai tags de estilo.
# 5. Salva no banco para a API servir de manhã.

import os
import requests
import json
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


def buscar_obras_chicago(termo: str, limite: int = 15) -> list[dict]:
    """
    Busca obras na API do Art Institute of Chicago.
    Filtra apenas obras com imagem disponível (is_public_domain).
    """
    print(f"🏛️ Buscando no Art Institute of Chicago: {termo}")

    params = {
        "q": termo,
        "fields": "id,title,image_id,artist_title,style_titles,classification_titles,is_public_domain,term_titles",
        "limit": limite,
    }

    resp = requests.get(f"{ARTIC_API_URL}/artworks/search", params=params)
    if resp.status_code != 200:
        print(f"❌ Erro na busca: {resp.text}")
        return []

    dados = resp.json()
    iiif_url = dados.get("config", {}).get("iiif_url", ARTIC_IIIF_URL)
    items = dados.get("data", [])

    # Filtra apenas obras que têm imagem disponível
    obras = []
    for item in items:
        image_id = item.get("image_id")
        if not image_id:
            continue

        # URL da imagem via IIIF
        image_url = f"{iiif_url}/{image_id}/full/843,/0/default.jpg"

        # Extrai estilos/termos disponíveis da API
        estilos = item.get("style_titles", []) or []
        termos = item.get("term_titles", []) or []
        classificacao = item.get("classification_titles", []) or []
        todas_tags = estilos + termos + classificacao

        obras.append({
            "titulo_original": item.get("title", "Untitled"),
            "artista": item.get("artist_title", "Unknown"),
            "image_id": image_id,
            "image_url": image_url,
            "tags_api": todas_tags[:5],  # Máximo 5 tags da API
        })

    print(f"✅ Encontradas {len(obras)} obras com imagem")
    return obras


def traduzir_e_taguear(obras: list[dict]) -> list[dict]:
    """
    Usa o GPT para traduzir títulos e criar tags em português.
    Não envia imagens — usa apenas os metadados da API.
    Muito mais barato que o GPT-4o Vision!
    """
    if not obras:
        return []

    print("🧠 Pedindo ao GPT para traduzir e taguear...")

    lista_obras = []
    for i, obra in enumerate(obras):
        lista_obras.append({
            "index": i,
            "titulo": obra["titulo_original"],
            "artista": obra["artista"],
            "tags_api": obra["tags_api"],
        })

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Você é um curador de arte. Receba esta lista de obras e retorne "
                    "um JSON com a chave 'obras' contendo um array. Para cada obra, "
                    "inclua: 'index' (o índice original), 'titulo' (título criativo "
                    "traduzido para português, pode ser poético), 'tags' (3 palavras-chave "
                    "de estilo/cor/técnica em português, separadas por vírgula). "
                    "Selecione apenas as 10 mais interessantes.\n\n"
                    f"Obras: {json.dumps(lista_obras, ensure_ascii=False)}"
                ),
            }
        ],
    )

    resultado = json.loads(resposta.choices[0].message.content)
    obras_traduzidas = resultado.get("obras", [])
    print(f"🎨 GPT selecionou e traduziu {len(obras_traduzidas)} obras")
    return obras_traduzidas


def rodar_curadoria():
    """Pipeline completo de curadoria diária."""
    print("=" * 50)
    print("🤖 ROBÔ CURADOR — Iniciando curadoria do dia")
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
            else "impressionism, abstract, contemporary painting"
        )
        print(f"💭 Gostos atuais: {gosto_str}")

        # 2. Pede ao GPT para gerar o termo de busca em inglês
        resp_termo = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Crie um termo de busca curto em inglês para encontrar "
                        f"obras de arte focadas nestes estilos: {gosto_str}. "
                        f"Retorne APENAS o termo, sem aspas ou explicações."
                    ),
                }
            ],
        )
        termo = resp_termo.choices[0].message.content.strip().strip('"')
        print(f"🔎 Termo gerado: {termo}")

        # 3. Busca no Art Institute of Chicago
        obras_encontradas = buscar_obras_chicago(termo)
        if not obras_encontradas:
            print("⚠️ Nenhuma obra encontrada. Encerrando.")
            return

        # 4. GPT traduz e tagueia (sem Vision — usa metadados)
        obras_traduzidas = traduzir_e_taguear(obras_encontradas)

        # 5. Salva no Banco de Dados
        hoje = date.today()
        for obra_trad in obras_traduzidas:
            idx = obra_trad.get("index", 0)
            if idx < len(obras_encontradas):
                obra_original = obras_encontradas[idx]
                # Salva o image_id para proxy pela nossa API
                nova_obra = Obra(
                    titulo=obra_trad.get("titulo", "Sem título"),
                    imagem_url=obra_original["image_id"],  # Salva apenas o ID
                    tags_extraidas=obra_trad.get("tags", ""),
                    data_exibicao=hoje,
                )
                db.add(nova_obra)

        db.commit()
        count = len(obras_traduzidas)
        print(f"\n🎨 Curadoria concluída! {count} obras salvas para hoje.")

    except Exception as e:
        print(f"❌ Erro na curadoria: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    rodar_curadoria()
