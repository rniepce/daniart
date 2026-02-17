# curador.py — Robô Curador (O Chef da Madrugada)
# Roda como Cron Job às 04:00 AM.
# 1. Lê o perfil de gosto (o que ela tem curtido).
# 2. Pede ao GPT um termo de busca em inglês.
# 3. Busca imagens no Google Custom Search.
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
# CHAVES DE API (use variáveis de ambiente em produção!)
# ──────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-sua-chave-openai-aqui")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "sua-chave-google-aqui")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "seu-cx-google-aqui")

client = OpenAI(api_key=OPENAI_API_KEY)


def buscar_imagens_google(termo: str) -> list[str]:
    """Busca imagens no Google Custom Search API."""
    print(f"🔍 Buscando no Google por: {termo}")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": termo,
        "cx": SEARCH_ENGINE_ID,
        "key": GOOGLE_API_KEY,
        "searchType": "image",
        "imgSize": "large",
        "num": 10,
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"❌ Erro na busca: {resp.text}")
        return []
    return [item["link"] for item in resp.json().get("items", [])]


def filtrar_com_visao(urls: list[str]) -> list[dict]:
    """
    Envia imagens para o GPT-4o Vision.
    Ele curadoria: descarta arte digital, fotos de pessoas, molduras vazias.
    Retorna apenas pinturas físicas reais com título e tags.
    """
    print("🧠 Enviando para o GPT-4o Vision escolher as melhores...")

    conteudo = [
        {
            "type": "text",
            "text": (
                "Você é um curador de arte de elite. "
                "Analise cada imagem e retorne um JSON com a chave 'obras' "
                "contendo APENAS as melhores pinturas físicas reais desta lista. "
                "Descarte arte digital, fotos de pessoas ou molduras vazias. "
                "Para cada obra aprovada, inclua: "
                "'url' (a URL original da imagem), "
                "'titulo' (título criativo em português), "
                "'tags' (3 palavras-chave de estilo/cor separadas por vírgula, "
                "ex: 'impasto, abstrato, azul')."
            ),
        }
    ]

    for url in urls[:10]:
        conteudo.append({"type": "image_url", "image_url": {"url": url}})

    resposta = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": conteudo}],
    )

    resultado = json.loads(resposta.choices[0].message.content)
    obras = resultado.get("obras", [])
    print(f"✅ GPT-4o Vision aprovou {len(obras)} obras")
    return obras


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
            else "contemporary heavy texture abstract painting"
        )
        print(f"💭 Gostos atuais: {gosto_str}")

        # 2. Pede ao GPT para gerar o termo de busca em inglês
        resp_termo = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Crie um termo de busca curto em inglês para o Google Imagens "
                        f"focado nestes estilos de arte: {gosto_str}. "
                        f"Retorne APENAS o termo, sem aspas ou explicações."
                    ),
                }
            ],
        )
        termo = resp_termo.choices[0].message.content.strip().strip('"')
        print(f"🔎 Termo gerado: {termo}")

        # 3. Busca no Google e filtra com visão
        urls_brutas = buscar_imagens_google(termo)
        if not urls_brutas:
            print("⚠️ Nenhuma imagem encontrada. Encerrando.")
            return

        obras_aprovadas = filtrar_com_visao(urls_brutas)

        # 4. Salva no Banco de Dados
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
