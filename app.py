import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2 import service_account
from datetime import datetime, date, time
import pytz

st.set_page_config(page_title="Dom Barber Shop", page_icon="💈", layout="wide")

st.markdown("""
<style>
:root { --bg:#0f0f12; --card:#17171c; --accent:#d4af37; --text:#f2f2f2; --muted:#9aa0a6;}
.stApp {background: radial-gradient(1200px 600px at 10% 0%, #14141a 0%, var(--bg) 35%, #0b0b0e 100%) !important;}
.block-container {padding-top:1.2rem; padding-bottom:3rem;}
h1, h2, h3, h4 {color: var(--text);}
div[data-baseweb="input"] input, .stTextArea textarea, .stSelectbox div, .stDateInput input, .stNumberInput input, .stMultiSelect div {color: var(--text) !important;}
.css-ue6h4q, .stSelectbox div[data-baseweb="select"] {color: var(--text) !important;}
.sidebar .sidebar-content {background: var(--card);}
.stButton>button {background: var(--accent); color:#111; font-weight:700; border-radius:12px; padding:0.6rem 1rem;}
.stTabs [data-baseweb="tab-list"] {gap:8px;}
.stTabs [data-baseweb="tab"] {background:var(--card); border-radius:999px; padding:8px 14px; border:1px solid #2a2a33; color:var(--text);}
.stTabs [aria-selected="true"] {border-color: var(--accent); color: var(--accent);}
.card {background: var(--card); border:1px solid #24242b; border-radius:18px; padding:18px;}
.kpi {background: linear-gradient(180deg,#1e1e25 0%, #15151b 100%); border:1px solid #262631; border-radius:16px; padding:16px;}
.kpi h3 {margin:0; color:var(--muted); font-weight:600; font-size:0.9rem;}
.kpi .v {font-size:1.8rem; font-weight:800; color:var(--accent);}
.header {display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;}
.header h1 {margin:0;}
.badge {background: #22222a; border:1px solid #2e2e39; color: var(--muted); padding:6px 10px; border-radius:999px; font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

tz = pytz.timezone("America/Sao_Paulo")

def get_client():
    creds_info = st.secrets["gcp_service_account"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    return gspread.authorize(creds)

def get_sheet():
    gc = get_client()
    title = st.secrets.get("SPREADSHEET_TITLE","Dom Barber Shop")
    try:
        sh = gc.open(title)
    except Exception:
        sh = gc.create(title)
    return sh

def ensure_ws(sh, title, headers):
    try:
        ws = sh.worksheet(title)
    except Exception:
        ws = sh.add_worksheet(title=title, rows=1000, cols=max(10,len(headers)))
        ws.append_row(headers)
    vals = ws.row_values(1)
    if vals != headers:
        ws.clear()
        ws.append_row(headers)
    return ws

def load_df(ws):
    recs = ws.get_all_records()
    return pd.DataFrame(recs)

def append_row(ws, row):
    ws.append_row(row, value_input_option="USER_ENTERED")

def number(x):
    try:
        return float(x)
    except:
        return 0.0

sh = get_sheet()
ws_clientes = ensure_ws(sh, "Clientes", ["id","nome","telefone","email","nascimento","criado_em"])
ws_barbeiros = ensure_ws(sh, "Barbeiros", ["nome","telefone","comissao","ativo","criado_em"])
ws_servicos = ensure_ws(sh, "Servicos", ["servico","preco","descricao","ativo","criado_em"])
ws_atend = ensure_ws(sh, "Atendimentos", ["data","hora","barbeiro","cliente_id","cliente","servico","valor","pagamento","obs","timestamp"])

df_clientes = load_df(ws_clientes)
df_barbeiros = load_df(ws_barbeiros)
df_servicos = load_df(ws_servicos)
df_atend = load_df(ws_atend)

st.sidebar.markdown('<div class="card"><h3 style="margin-top:0;color:#f2f2f2;">💈 Dom Barber Shop</h3><div class="badge">Sistema</div></div>', unsafe_allow_html=True)
modo = st.sidebar.radio("Acesso", ["Barbeiro","Dono"], horizontal=True)
st.sidebar.divider()
st.sidebar.markdown("**Planilha:**")
try:
    st.sidebar.link_button("Abrir no Google Sheets", sh.url)
except:
    st.sidebar.write("Configure o Google Sheets nas `secrets`.")

st.markdown('<div class="header"><h1>💈 Dom Barber Shop</h1><div class="badge">Visual Premium</div></div>', unsafe_allow_html=True)

if modo == "Barbeiro":
    colA, colB = st.columns([1,2])
    with colA:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        lista_barbeiros = [""] + sorted(df_barbeiros[df_barbeiros["ativo"].astype(str).str.lower().eq("true")]["nome"].tolist()) if not df_barbeiros.empty else [""]
        barbeiro_nome = st.selectbox("Barbeiro", options=lista_barbeiros, index=0, placeholder="Selecione ou digite")
        if barbeiro_nome == "":
            barbeiro_nome = st.text_input("Novo Barbeiro (caso não esteja na lista)", "")
            if st.button("Cadastrar Barbeiro"):
                if barbeiro_nome.strip():
                    append_row(ws_barbeiros, [barbeiro_nome.strip(),"","0.0","True",datetime.now(tz).isoformat()])
                    df_barbeiros = load_df(ws_barbeiros)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with colB:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Cadastro de Cliente + Atendimento")
        with st.form("form_cli_atend", clear_on_submit=True):
            nome = st.text_input("Nome do Cliente")
            telefone = st.text_input("Telefone")
            email = st.text_input("Email")
            nascimento = st.date_input("Nascimento", value=None)
            servicos_opts = sorted(df_servicos[df_servicos["ativo"].astype(str).str.lower().eq("true")]["servico"].tolist()) if not df_servicos.empty else []
            serv = st.selectbox("Serviço", options=servicos_opts, index=0 if servicos_opts else None, placeholder="Cadastrar em 'Serviços' no acesso Dono")
            preco_base = 0.0
            if serv:
                row = df_servicos[df_servicos["servico"]==serv].head(1)
                preco_base = number(row["preco"].iloc[0]) if not row.empty else 0.0
            valor = st.number_input("Valor (R$)", value=float(preco_base), min_value=0.0, step=1.0, format="%.2f")
            pagamento = st.selectbox("Pagamento", ["Dinheiro","Cartão","Pix","Outro"])
            obs = st.text_area("Observações", height=80)
            enviar = st.form_submit_button("Salvar e Registrar Atendimento")
        if enviar:
            if not barbeiro_nome.strip():
                st.error("Informe o nome do Barbeiro.")
            elif not nome.strip() or not serv:
                st.error("Informe nome do cliente e selecione o serviço.")
            else:
                now = datetime.now(tz)
                hoje = now.date().isoformat()
                hora = now.strftime("%H:%M:%S")
                if df_clientes.empty:
                    next_id = 1
                else:
                    try:
                        next_id = int(max(pd.to_numeric(df_clientes["id"], errors="coerce").fillna(0)))+1
                    except:
                        next_id = len(df_clientes)+1
                cli_exist = None
                if not df_clientes.empty and telefone.strip():
                    m = df_clientes["telefone"].astype(str).str.replace(r"\D","",regex=True)==pd.Series([telefone]).astype(str).str.replace(r"\D","",regex=True).iloc[0]
                    if m.any():
                        cli_exist = df_clientes[m].iloc[0]
                        next_id = cli_exist["id"]
                if cli_exist is None:
                    append_row(ws_clientes, [str(next_id), nome.strip(), telefone.strip(), email.strip(), nascimento.isoformat() if isinstance(nascimento,date) else "", now.isoformat()])
                append_row(ws_atend, [hoje, hora, barbeiro_nome.strip(), str(next_id), nome.strip(), serv, float(valor), pagamento, obs.strip(), now.isoformat()])
                st.success("Cliente salvo e atendimento registrado.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("### Log diário do Barbeiro")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if df_atend.empty:
        st.info("Sem atendimentos.")
    else:
        today = datetime.now(tz).date().isoformat()
        dfa = df_atend.copy()
        dfa_today = dfa[dfa["data"]==today]
        if barbeiro_nome.strip():
            dfa_today = dfa_today[dfa_today["barbeiro"]==barbeiro_nome.strip()]
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="kpi"><h3>Atendimentos Hoje</h3><div class="v">{len(dfa_today)}</div></div>', unsafe_allow_html=True)
        receita = dfa_today["valor"].apply(number).sum() if not dfa_today.empty else 0.0
        c2.markdown(f'<div class="kpi"><h3>Receita Hoje (R$)</h3><div class="v">{receita:,.2f}</div></div>', unsafe_allow_html=True)
        serv_count = dfa_today["servico"].value_counts().head(1)
        top = serv_count.index[0] if not serv_count.empty else "-"
        c3.markdown(f'<div class="kpi"><h3>Serviço Mais Feito</h3><div class="v">{top}</div></div>', unsafe_allow_html=True)
        st.dataframe(dfa_today.sort_values(["hora"], ascending=False), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    tabs = st.tabs(["Relatórios","Dashboards","Barbeiros","Serviços","Dados"])
    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if df_atend.empty:
            st.info("Sem dados de atendimentos.")
        else:
            dfa = df_atend.copy()
            dfa["valor"] = dfa["valor"].apply(number)
            cortes_dia = dfa.groupby("data").size().reset_index(name="cortes")
            finan_dia = dfa.groupby("data")["valor"].sum().reset_index(name="receita")
            c1,c2 = st.columns(2)
            c1.subheader("Cortes por dia")
            c1.dataframe(cortes_dia.sort_values("data", ascending=False), use_container_width=True)
            c2.subheader("Financeiro por dia (R$)")
            c2.dataframe(finan_dia.sort_values("data", ascending=False), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if df_atend.empty:
            st.info("Sem dados para dashboards.")
        else:
            dfa = df_atend.copy()
            dfa["valor"] = dfa["valor"].apply(number)
            dfa["data"] = pd.to_datetime(dfa["data"], errors="coerce")
            ult = dfa[dfa["data"]>= (pd.Timestamp(datetime.now(tz).date()) - pd.Timedelta(days=30))]
            k1,k2,k3,k4 = st.columns(4)
            total_at = len(ult)
            receita = ult["valor"].sum()
            ticket = (receita/total_at) if total_at>0 else 0.0
            barbeiros_ativos = ult["barbeiro"].nunique()
            k1.markdown(f'<div class="kpi"><h3>Atendimentos (30d)</h3><div class="v">{total_at}</div></div>', unsafe_allow_html=True)
            k2.markdown(f'<div class="kpi"><h3>Receita (30d)</h3><div class="v">{receita:,.2f}</div></div>', unsafe_allow_html=True)
            k3.markdown(f'<div class="kpi"><h3>Ticket Médio</h3><div class="v">{ticket:,.2f}</div></div>', unsafe_allow_html=True)
            k4.markdown(f'<div class="kpi"><h3>Barbeiros Ativos</h3><div class="v">{barbeiros_ativos}</div></div>', unsafe_allow_html=True)
            g1,g2 = st.columns(2)
            by_day = ult.groupby(ult["data"].dt.date).agg(atend=("servico","size"), receita=("valor","sum")).reset_index().rename(columns={"data":"dia"})
            fig1 = px.line(by_day, x="data", y="atend", markers=True, title="Atendimentos por dia")
            fig2 = px.line(by_day, x="data", y="receita", markers=True, title="Receita por dia (R$)")
            g1.plotly_chart(fig1, use_container_width=True)
            g2.plotly_chart(fig2, use_container_width=True)
            svc = ult.groupby("servico")["valor"].sum().reset_index().sort_values("valor", ascending=False)
            fig3 = px.pie(svc, names="servico", values="valor", title="Receita por serviço")
            st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Cadastro de Barbeiro")
        with st.form("form_barbeiro"):
            b_nome = st.text_input("Nome do Barbeiro")
            b_tel = st.text_input("Telefone")
            b_com = st.number_input("Comissão (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, format="%.2f")
            b_ativo = st.checkbox("Ativo", value=True)
            b_enviar = st.form_submit_button("Salvar Barbeiro")
        if b_enviar and b_nome.strip():
            append_row(ws_barbeiros, [b_nome.strip(), b_tel.strip(), str(b_com), "True" if b_ativo else "False", datetime.now(tz).isoformat()])
            st.success("Barbeiro cadastrado.")
            st.rerun()
        st.divider()
        st.subheader("Lista")
        if df_barbeiros.empty:
            st.info("Sem registros.")
        else:
            st.dataframe(df_barbeiros.sort_values("criado_em", ascending=False), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Cadastro de Serviço")
        with st.form("form_serv"):
            s_nome = st.text_input("Serviço")
            s_preco = st.number_input("Preço (R$)", min_value=0.0, step=1.0, format="%.2f")
            s_desc = st.text_input("Descrição")
            s_ativo = st.checkbox("Ativo", value=True)
            s_enviar = st.form_submit_button("Salvar Serviço")
        if s_enviar and s_nome.strip():
            append_row(ws_servicos, [s_nome.strip(), float(s_preco), s_desc.strip(), "True" if s_ativo else "False", datetime.now(tz).isoformat()])
            st.success("Serviço cadastrado.")
            st.rerun()
        st.divider()
        st.subheader("Lista")
        if df_servicos.empty:
            st.info("Sem registros.")
        else:
            st.dataframe(df_servicos.sort_values("criado_em", ascending=False), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with tabs[4]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Dados Brutos")
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**Clientes**")
            st.dataframe(df_clientes, use_container_width=True)
            st.markdown("**Barbeiros**")
            st.dataframe(df_barbeiros, use_container_width=True)
        with c2:
            st.markdown("**Serviços**")
            st.dataframe(df_servicos, use_container_width=True)
            st.markdown("**Atendimentos**")
            st.dataframe(df_atend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
