<!-- Badges -->
<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.10+-009688?logo=fastapi" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/github/actions/workflow/status/OWNER/REPO/ci.yml?label=CI&logo=github" />
</p>

<h1 align="center">Letrus – Comparação de Textos (Plágio / Paráfrase)</h1>

<p align="center">
Solução simples para comparar um texto de aluno contra um pequeno corpus de artigos da Wikipedia (PT-BR) usando abordagens léxica (TF‑IDF + cosseno) e semântica (embeddings <code>sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2</code>).
</p>

---

## 🔖 Sumário
- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Stack e Modelos](#-stack-e-modelos)
- [Instalação Rápida](#-instalação-rápida)
- [Uso da API](#-uso-da-api)
- [Docker](#-docker)
- [Pipeline CI](#-pipeline-ci)
- [Estrutura de Pastas](#-estrutura-de-pastas)
- [Notas & Dicas](#-notas--dicas)
- [Próximas Ideias](#-próximas-ideias)

## 🧭 Visão Geral
> Foco: protótipo leve para detecção inicial de similaridade / potencial plágio via comparação com ~200 artigos públicos PT-BR.

A comparação retorna TOP-K documentos similares em duas dimensões:
1. Léxico: TF-IDF + similaridade de cosseno.
2. Semântico: embeddings Sentence-Transformers multilíngues.

## ✅ Funcionalidades
- `GET /health` – status
- `POST /compare` – recebe `{ text, top_k }`
- `POST /reload` – reconstrói índice (após alterar variáveis de dataset)
- Carregamento automático do subset Wikipedia (Hugging Face `datasets`)
- Cache local em diretório padrão Hugging Face (`~/.cache/huggingface`)

## 🧱 Stack e Modelos
| Componente | Tecnologia |
|------------|------------|
| API | FastAPI + Uvicorn |
| Vetorização Léxica | scikit-learn (TfidfVectorizer) |
| Embeddings | sentence-transformers (MiniLM Multilingual) |
| Dataset | `wikipedia` (subset PT-BR, tamanho configurável) |
| Testes | pytest |
| Infra (container) | Docker |

## ⚙️ Instalação Rápida

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .[dev]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Variáveis de Ambiente Principais
| Nome | Descrição | Exemplo |
|------|-----------|---------|
| DATASET_LANG | Código de língua | pt |
| DATASET_SIZE | Quantidade de artigos | 200 |
| WIKIPEDIA_DATES | (Opcional) Filtro de datas | 20231101 |

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

### Recarregar Índice
```powershell
curl -X POST http://localhost:8000/reload
```

<details>
<summary><strong>Exemplo de Resposta (parcial)</strong></summary>

```json
{
  "lexical": [
    {"doc_id": 42, "score": 0.612, "title": "Revolução Industrial"},
    {"doc_id": 7,  "score": 0.401, "title": "Inglaterra"}
  ],
  "semantic": [
    {"doc_id": 42, "score": 0.812, "title": "Revolução Industrial"},
    {"doc_id": 15, "score": 0.676, "title": "Máquinas a vapor"}
  ]
}
```
</details>

## 🐳 Docker

### Build
```powershell
docker build -t letrus-plagiarism:latest .
```

### Run
```powershell
docker run --rm -p 8000:8000 letrus-plagiarism:latest
```

### Cache de Modelos
> Recomendado fazer um primeiro build conectado à internet. Camada de cache reaproveitada em builds subsequentes.

## 🔁 Pipeline CI
- Executa testes (pytest)
- Build da imagem Docker
- (Opcional futuro) push para registry

Consultar `.github/workflows/ci.yml`.

## 🗂️ Estrutura de Pastas
```text
app/
  main.py          # Entrypoint FastAPI
  data.py          # Carrega dataset + cache
  compare.py       # Lógica de similaridade
  models.py        # Pydantic schemas
tests/
  test_compare.py
  test_api.py
```

## 💡 Notas & Dicas
> Primeira execução baixa modelo e dataset (pode levar alguns minutos).

- Rodar uma vez online e depois reutilizar cache offline.
- Ajustar `top_k` conforme necessidade (default implementado no modelo de request).
- Monitorar memória se `DATASET_SIZE` crescer.

## 🚀 Próximas Ideias
- Paginação / streaming de resultados
- Normalização de pontuação conjunta (score híbrido)
- Métricas de benchmarking (MAP / nDCG)
- Suporte a outros modelos (e.g. bge-m3, e5-multilingual)
- Persistência incremental do índice

## 🧭 Arquitetura
Detalhes em: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

<p align="center">
Feito para experimentação educacional e detecção preliminar. Não substitui revisão