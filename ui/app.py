import difflib
from typing import Dict, Any, List
import streamlit as st
import requests
import os 


API_BASE = os.environ.get("API_BASE", "http://api:8000")

# ---------------------------------- Config ----------------------------------
st.set_page_config(page_title="Detector de Similaridade Wikipedia", page_icon="🔎", layout="wide")


def fetch_results(text: str, top_k: int) -> Dict[str, Any]:
    payload = {"text": text, "top_k": top_k}
    try:
        r = requests.post(f"{API_BASE}/compare", json=payload)
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
    input_text = st.text_area('Texto (query)', height=160, key='query_text')
    c1, c2 = st.columns(2)
    with c1:
        top_k = st.number_input('top_k', min_value=1, max_value=50)
        if st.button('Buscar', type='primary'):
            with st.spinner('Consultando...'):
                st.session_state['results'] = fetch_results(input_text, int(top_k))

    # with c2:
    #     if st.button('Buscar', type='primary'):
    #         with st.spinner('Consultando...'):
    #             st.session_state['results'] = fetch_results(input_text, int(top_k))

# ---------------------------------- Main ------------------------------------
st.title('🔎 Detector de Similaridade / Plágio (Wikipedia)')
st.write('Visualização de similaridade lexical e semântica (agrupadas por documento).')

mc = st.columns(3)
with mc[0]:
    st.metric('Chars Texto', len(input_text))
with mc[1]:
    st.metric('top_k', top_k)

with st.expander('Mostrar Texto Original', expanded=False):
    st.write(input_text)

results: Dict[str, Any] = st.session_state.get('results', {})
if results:
    render_results(results)
else:
    st.info('Clique em Buscar para obter resultados do backend.')

st.markdown('---')
