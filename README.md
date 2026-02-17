# ArtAdvisor 🎨

Curadoria de arte personalizada com IA — 3 frentes integradas.

## Estrutura

```
artadvisor/          → Backend Python (FastAPI + SQLAlchemy)
ArtAdvisor/          → App iPhone (SwiftUI)
```

## Como rodar

### Backend

```bash
cd artadvisor
pip3 install -r requirements.txt
python3 -m uvicorn main:app --reload
```

### App iPhone

Abra `ArtAdvisor/ArtAdvisor.xcodeproj` no Xcode → Run
