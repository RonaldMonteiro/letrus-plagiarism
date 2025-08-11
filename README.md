<!-- Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.10+-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/github/actions/workflow/status/OWNER/REPO/ci.yml?label=CI&logo=github" />
</p>

<h1 align="center">Letrus – Detecção de plágio em pt-BR</h1>

<p align="center">
Solução simples para comparar um texto de aluno contra um pequeno corpus de artigos da Wikipedia (PT-BR) usando abordagens léxica (TF‑IDF + cosseno) e semântica (embeddings <code>sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2</code>).
</p>

---

## 🔖 Sumário
- [Visão geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Stacks](#-stacks)
- [Primeiros passos](#-primeiro-passos)
- [Uso da API](#-uso-da-api)
- [Pipeline CI](#-pipeline-ci)

## 🧭 Visão geral
> Foco: protótipo leve para detecção inicial de similaridade / potencial plágio via comparação com ~200 artigos públicos PT-BR.

A comparação retorna TOP-K documentos similares em duas dimensões:
1. Léxico: TF-IDF + similaridade de cosseno.
2. Semântico: embeddings Sentence-Transformers multilíngues.

## ✅ Funcionalidades
- `GET /health` – status
- `POST /compare` – recebe `{ text, top_k }`

## 🧱 Stacks
| Componente | Tecnologia |
|------------|------------|
| API | FastAPI + Uvicorn |
| Vetorização Léxica | scikit-learn (TfidfVectorizer) |
| Embeddings | sentence-transformers (MiniLM Multilingual) |
| Dataset | `wikipedia` (subset PT-BR, tamanho configurável) |
| Testes | pytest |
| Infra (container) | Docker |
| Interface | Streamlit |

## 🗂️ Estrutura de pastas
```text
api/
  data.py           # Carrega dataset + cache
  main.py           # Entrypoint FastAPI
  match.py          # Lógica de comparação (similaridade)
  split.py          # Utilitários de divisão de dados/texto
  models/           # Schemas Pydantic
  tests/            # Testes unitários (pytest)
  utils/            # Funções auxiliares
  Dockerfile        # Container API
  pyproject.toml    # Dependências PPI

ui/
  app.py            # Interface Streamlit
  Dockerfile        # Container UI
  pyproject.toml    # Dependências UI
Dockerfile          # Container API
docker-compose.yml  # Orquestração dos serviços
LICENSE
pytest.ini
README.md
```

## ⚙️ Primeiros passos
A forma mais prática de iniciar os serviços é rodando o comando abaixo na raiz do projeto, utilizando o docker compose:

```bash
docker compose up -d
```

Durante o desenvolvimento, você pode iniciar cada aplicação separadamente utilizando o gerenciador de pacotes uv:

##### API
```powershell
cd api
pip install uv
uv sync
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

##### UI
```powershell
cd ui
pip install uv
uv sync
source .venv/bin/activate
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

## 🛰️ Uso da API

### Health
```powershell
curl http://localhost:8000/health
```

### Compare
```powershell
curl -X POST http://localhost:8000/compare -H "Content-Type: application/json" -d "{ \`
  \"text\": \"A Revolução Industrial começou na Inglaterra...\", \`
  \"top_k\": 5 \`
}"
```


## 🔁 Pipeline CI
- Executa testes (pytest)
- Build da imagem Docker

Consultar `.github/workflows/ci.yml`.