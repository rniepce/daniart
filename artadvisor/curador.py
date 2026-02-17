# curador.py — Robô Curador (O Chef da Madrugada)
# Roda como agendamento automático às 04:00 AM.
# 1. Lê o perfil de gosto (o que ela tem curtido).
# 2. Pede ao GPT um termo de busca em inglês.
# 3. Busca obras na API gratuita do Art Institute of Chicago.
# 4. GPT-4o Vision filtra e seleciona as melhores pinturas.
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
ARTIC_IMAGE_URL = "https://www.artic.edu/iiif/2"


def buscar_obras_chicago(termo: str, limite: int = 15) -> list[dict]:
    """
    Busca obras na API do Art Institute of Chicago.
    Retorna lista com título, image_id e URL da imagem em alta resolução.
    """
    print(f"🏛️ Buscando no Art Institute of Chicago: {termo}")

    params = {
        "q": termo,
        "fields": "id,title,image_id,artist_title,style_titles,classification_titles",
        "limit": limite,
    }

    resp = requests.get(f"{ARTIC_API_URL}/artworks/search", params=params)
    if resp.status_code != 200:
        print(f"❌ Erro na busca: {resp.text}")
        return []

    dados = resp.json().get("data", [])

    # Filtra apenas obras que têm imagem disponível
    obras = []
    for item in dados:
        if not item.get("image_id"):
            continue

        image_url = f"{ARTIC_IMAGE_URL}/{item['image_id']}/full/843,/0/default.jpg"

        obras.append({
            "titulo": item.get("title", "Sem título"),
            "artista": item.get("artist_title", "Desconhecido"),
            "url": image_url,
            "estilos": item.get("style_titles", []),
            "classificacao": item.get("classification_titles", []),
        })

    print(f"✅ Encontradas {len(obras)} obras com imagem")
    return obras


def filtrar_com_visao(obras: list[dict]) -> list[dict]:
    """
    Envia imagens para o GPT-4o Vision.
    Ele seleciona as melhores e extrai tags de estilo.
    """
    if not obras:
        return []

    print("🧠 Enviando para o GPT-4o Vision curar as melhores...")

    conteudo = [
        {
            "type": "text",
            "text": (
                "Você é um curador de arte de elite. Analise estas obras do "
                "Art Institute of Chicago. Selecione as 10 mais impactantes "
                "visualmente — priorize pinturas com textura, cor vibrante e "
                "composição marcante. Retorne um JSON com a chave 'obras' "
                "contendo para cada obra selecionada: "
                "'url' (URL da imagem, copie exatamente como recebeu), "
                "'titulo' (título criativo em português), "
                "'tags' (3 palavras-chave de estilo/cor separadas por vírgula, "
                "ex: 'impasto, abstrato, azul')."
            ),
        }
    ]

    for obra in obras[:12]:
        conteudo.append({
            "type": "image_url",
            "image_url": {"url": obra["url"]}
        })

    resposta = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": conteudo}],
    )

    resultado = json.loads(resposta.choices[0].message.content)
    aprovadas = resultado.get("obras", [])
    print(f"🎨 GPT-4o Vision selecionou {len(aprovadas)} obras")
    return aprovadas


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

        # 4. GPT-4o Vision filtra as melhores
        obras_aprovadas = filtrar_com_visao(obras_encontradas)

        # 5. Salva no Banco de Dados
        hoje = date.today()
        for obra_data in obras_aprovadas:
            nova_obra = Obra(
                titulo=obra_data.get("titulo", "Sem título"),
                imagem_url=obra_data.get("url", ""),
                tags_extraidas=obra_data.get("tags", ""),
                data_exibicao=hoje,
            )
            db.add(nova_obra)

        db.commit()
        print(f"\n🎨 Curadoria concluída! {len(obras_aprovadas)} obras salvas para hoje.")

    except Exception as e:
        print(f"❌ Erro na curadoria: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    rodar_curadoria()
