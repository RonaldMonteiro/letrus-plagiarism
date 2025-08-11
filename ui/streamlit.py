import json
import difflib
from typing import Dict, Any, List
import streamlit as st
import requests  # fallback HTTP
import os  # added
import socket  # diagnóstico
import asyncio  # novo
import inspect  # novo
import time  # novo

# Tentativa de importar funções internas da API para chamada direta
HAVE_LOCAL_API = False
try:  # nomes comuns; ajuste se necessário
    from api import match as backend_match
    from api.main import health as backend_health
    HAVE_LOCAL_API = True
except Exception:  # noqa: BLE001
    try:
        # fallback alternativo: endpoints possivelmente definidos em outro módulo
        from api import match as backend_match  # type: ignore
        from api.main import health as backend_health  # type: ignore
        HAVE_LOCAL_API = True
    except Exception:  # noqa: BLE001
        HAVE_LOCAL_API = False

# ---------------------------------- Config ----------------------------------
st.set_page_config(page_title="Detector de Similaridade Wikipedia", page_icon="🔎", layout="wide")

SAMPLE_INPUT_REQUEST = {
    "text": "Carl Edward Sagan (Nova Iorque — Seattle) foi um renomado cientista planetário, astrônomo, astrobiólogo, astrofísico, escritor, divulgador científico e ativista norte-americano.",
    "top_k": 2,
    "detail": True
}

try:
    API_BASE = st.secrets["api_base"]  # pode lançar se não existir secrets
except Exception:
    API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

# Timeouts escalonados configuráveis: env HEALTH_TIMEOUTS="5,10,20"
RAW_HEALTH_TIMEOUTS = os.environ.get("HEALTH_TIMEOUTS", "5,10,20")
HEALTH_TIMEOUTS: List[float] = []
for part in RAW_HEALTH_TIMEOUTS.split(','):
    try:
        HEALTH_TIMEOUTS.append(float(part.strip()))
    except ValueError:  # noqa: PERF203
        pass
if not HEALTH_TIMEOUTS:
    HEALTH_TIMEOUTS = [5.0, 10.0, 20.0]

# Função única de preaquecer com diagnóstico detalhado
# Adaptada para usar função local se disponível + escalonamento de timeout.

def _call_local_health() -> Dict[str, Any]:
    try:
        res = backend_health()  # type: ignore[name-defined]
        if asyncio.iscoroutine(res):  # compat async
            res = asyncio.run(res)
        return {"ok": True, "status": 200, "data": res, "attempts": 1, "endpoint": "local:health"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": repr(e), "endpoint": "local:health"}

def preheat_health(retries: int | None = None, timeout: float | None = None) -> Dict[str, Any]:
    # retries/timeout mantidos por compat mas agora ignorados em favor de HEALTH_TIMEOUTS
    if HAVE_LOCAL_API:
        return _call_local_health()
    attempt = 0
    last_exc: Exception | None = None
    for t in HEALTH_TIMEOUTS:
        attempt += 1
        try:
            r = requests.get(f"{API_BASE}/health", timeout=t)
            ct = r.headers.get('content-type', '')
            data = r.json() if 'application/json' in ct else r.text
            return {"ok": r.ok, "status": r.status_code, "data": data, "attempts": attempt, "endpoint": f"{API_BASE}/health", "used_timeout": t}
        except Exception as e:  # noqa: BLE001
            last_exc = e
    # diagnóstico adicional de socket (host:port)
    host_port = API_BASE.replace('http://', '').replace('https://', '').split('/')[0]
    host, port = (host_port.split(':') + ['80'])[:2]
    sock_info: Dict[str, Any] = {}
    try:
        with socket.create_connection((host, int(port)), timeout=3):
            sock_info = {"tcp_connect": True}
    except Exception as se:  # noqa: BLE001
        sock_info = {"tcp_connect": False, "socket_error": repr(se)}
    err_repr = repr(last_exc) if last_exc else 'unknown error'
    return {
        "ok": False,
        "error": err_repr,
        "error_type": last_exc.__class__.__name__ if last_exc else None,
        "attempts": attempt,
        "endpoint": f"{API_BASE}/health",
        "timeouts_tried": HEALTH_TIMEOUTS,
        **sock_info,
        "hint": "Se o backend ainda está inicializando (carregando modelo / index), aumente HEALTH_TIMEOUTS ou aguarde." if sock_info.get("tcp_connect") else "Servidor não responde TCP. Está rodando?",
    }

def _call_local_match(text: str, top_k: int, detail: bool) -> Dict[str, Any]:
    req_payload = {"text": text, "top_k": top_k, "detail": detail}
    fn = backend_match  # type: ignore[name-defined]
    try:
        sig = inspect.signature(fn)
        if len(sig.parameters) == 1:
            # Tentar instanciar modelo pydantic se annotation indicar
            (param,) = sig.parameters.values()
            arg = req_payload
            ann = getattr(param, 'annotation', None)
            if ann and ann is not inspect._empty:  # noqa: SLF001
                ann_name = getattr(ann, '__name__', '').lower()
                if ann_name.endswith('request') or ann_name.endswith('matchrequest'):
                    try:
                        arg = ann(**req_payload)  # type: ignore[call-arg]
                    except Exception:  # noqa: BLE001
                        arg = req_payload
            res = fn(arg)
        else:
            res = fn(**req_payload)
        if asyncio.iscoroutine(res):
            res = asyncio.run(res)
        # Espera-se dicionário final
        return res if isinstance(res, dict) else dict(res)  # type: ignore[arg-type]
    except Exception as e:  # noqa: BLE001
        st.error(f'Erro função local match: {e}')
        return {}

def fetch_results(text: str, top_k: int, detail: bool) -> Dict[str, Any]:
    if HAVE_LOCAL_API:
        return _call_local_match(text, top_k, detail)
    payload = {"text": text, "top_k": top_k, "detail": detail}
    try:
        r = requests.post(f"{API_BASE}/compare", json=payload, timeout=max(HEALTH_TIMEOUTS[-1], 30))
        if r.status_code != 200:
            st.error(f"Erro backend {r.status_code}: {r.text[:300]}")
            return {}
        data = r.json()
        if 'items' not in data:
            st.warning('Resposta sem campo items.')
        return data
    except requests.Timeout:
        st.error('Timeout na requisição. Considere aumentar HEALTH_TIMEOUTS.')
    except Exception as e:  # noqa: BLE001
        st.error(f'Falha requisitando backend: {e}')
    return {}

# ---------------------------------- Helpers ---------------------------------

def highlight_diff(a: str, b: str) -> str:
    sm = difflib.SequenceMatcher(None, a, b)
    out: List[str] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            out.append(a[i1:i2])
        elif tag == 'insert':
            out.append(f"<span style='background:#d1fadf'>{b[j1:j2]}</span>")
        elif tag == 'delete':
            out.append(f"<span style='background:#ffe0e0;text-decoration:line-through'>{a[i1:i2]}</span>")
        else:  # replace
            out.append(f"<span style='background:#fff4cc'>{b[j1:j2]}</span>")
    return ''.join(out)

def score_color(score: float) -> str:
    if score >= 0.85: return '#047857'  # verde
    if score >= 0.7: return '#2563eb'   # azul
    if score >= 0.5: return '#d97706'   # âmbar
    return '#b91c1c'                   # vermelho

def show_doc(doc: Dict[str, Any]):
    st.markdown(f"### Doc {doc.get('doc_id')} • {doc.get('doc_title','(sem título)')}")
    sentences = doc.get('sentences', [])
    if not sentences:
        st.caption('Sem sentenças alinhadas.')
        return
    for i, s in enumerate(sentences, 1):
        with st.container():
            st.markdown(f"<div style='font-weight:600'>Sentença {i} • Score {s['score']:.3f}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.caption('Documento')
                st.write(s['doc_sentence'])
            with c2:
                st.caption('Query')
                st.write(s['query_sentence'])
            with st.expander('Diferenças', expanded=False):
                st.markdown(highlight_diff(s['doc_sentence'], s['query_sentence']), unsafe_allow_html=True)
            st.caption(f"Doc: [{s['doc_start']}, {s['doc_end']}] • Query: [{s['query_start']}, {s['query_end']}]")
            st.markdown('<hr/>', unsafe_allow_html=True)

def render_results(data: Dict[str, Any]):
    top_cols = st.columns(3)
    with top_cols[0]:
        st.metric('Chars Query', data.get('query_len'))
    with top_cols[1]:
        st.metric('Corpus Docs', data.get('corpus_size'))
    max_sem = 0.0
    for item in data.get('items', []):
        if item.get('method') == 'semantic':
            for doc in item.get('docs', []):
                for s in doc.get('sentences', []):
                    max_sem = max(max_sem, float(s.get('score', 0)))
    with top_cols[2]:
        st.metric('Max Score Sentença (Sem.)', f"{max_sem:.3f}")
    st.markdown('---')
    items = data.get('items', [])
    if not items:
        st.info('Sem resultados.')
        return
    tabs = st.tabs([i['method'].capitalize() for i in items])
    for tab, item in zip(tabs, items):
        with tab:
            st.subheader(f"Método: {item['method']}")
            docs = item.get('docs', [])
            if not docs:
                st.info('Sem documentos retornados (detail=False).')
            else:
                for doc in docs:
                    show_doc(doc)

# ---------------------------------- Sidebar ---------------------------------
st.sidebar.title('Configuração')
with st.sidebar:
    input_text = st.text_area('Texto (query)', SAMPLE_INPUT_REQUEST['text'], height=160, key='query_text')
    c1, c2 = st.columns(2)
    with c1:
        top_k = st.number_input('top_k', min_value=1, max_value=50, value=SAMPLE_INPUT_REQUEST['top_k'])
    with c2:
        detail = st.checkbox('detail', value=SAMPLE_INPUT_REQUEST['detail'])
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button('Buscar', type='primary'):
            with st.spinner('Consultando...'):
                st.session_state['results'] = fetch_results(input_text, int(top_k), bool(detail))
    with bcol2:
        if st.button('Preaquecer'):
            with st.spinner(f"Verificando health (timeouts {HEALTH_TIMEOUTS})..."):
                h = preheat_health()
            if h.get('ok'):
                st.success(f"Health OK ({h.get('status')}) em {h.get('attempts')} tentativa(s)")
                if 'used_timeout' in h:
                    st.caption(f"Timeout usado: {h['used_timeout']}s")
            else:
                st.error('Health Falhou')
                with st.expander('Detalhes do erro', expanded=False):
                    st.json(h)
    st.caption(f"Endpoint: {'local (funções)' if HAVE_LOCAL_API else API_BASE}")
    if not HAVE_LOCAL_API:
        st.caption('Ajuste env HEALTH_TIMEOUTS (ex: 5,10,30) se inicialização for lenta.')

# ---------------------------------- Main ------------------------------------
st.title('🔎 Detector de Similaridade / Plágio (Wikipedia)')
st.write('Visualização de similaridade lexical e semântica (agrupadas por documento).')

mc = st.columns(3)
with mc[0]:
    st.metric('Chars Texto', len(input_text))
with mc[1]:
    st.metric('top_k', top_k)
with mc[2]:
    st.metric('Detalhe', 'Sim' if detail else 'Não')

with st.expander('Mostrar Texto Original', expanded=False):
    st.write(input_text)

results: Dict[str, Any] = st.session_state.get('results', {})
if results:
    render_results(results)
else:
    st.info('Clique em Buscar para obter resultados do backend.')

st.markdown('---')
st.caption('Schema dinâmico: items[].docs[].sentences[].')
