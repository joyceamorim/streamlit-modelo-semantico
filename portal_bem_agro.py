import streamlit as st
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Bem Agro | Portal do Cliente",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para visual profissional
st.markdown("""
<style>
    /* Importar fonte */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    /* Reset e base */
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Esconder elementos padrão do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Sidebar customizada */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a472a 0%, #2d5a3d 100%);
        padding-top: 0;
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Logo container */
    .logo-container {
        padding: 2rem 1.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 1rem;
    }
    
    .logo-text {
        font-size: 1.8rem;
        font-weight: 700;
        color: white;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .logo-subtitle {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.25rem;
    }
    
    /* Menu items */
    .menu-item {
        padding: 0.875rem 1.5rem;
        margin: 0.25rem 0.75rem;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    .menu-item:hover {
        background: rgba(255,255,255,0.1);
    }
    
    .menu-item.active {
        background: rgba(255,255,255,0.15);
        border-left: 3px solid #4ade80;
    }
    
    /* Cards */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1rem;
    }
    
    .card-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
    }
    
    .card-date {
        font-size: 0.8rem;
        color: #6b7280;
    }
    
    .card-description {
        color: #4b5563;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    /* Badges/Tags */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-published {
        background: #dcfce7;
        color: #166534;
    }
    
    .badge-draft {
        background: #fef3c7;
        color: #92400e;
    }
    
    .badge-powerbi {
        background: #fef9c3;
        color: #854d0e;
    }
    
    /* Page header */
    .page-header {
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .page-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0 0 0.5rem 0;
    }
    
    .page-description {
        color: #6b7280;
        font-size: 0.95rem;
    }
    
    /* Botões customizados */
    .btn-primary {
        background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
        color: white;
        padding: 0.625rem 1.25rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.875rem;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        transition: all 0.2s ease;
        border: none;
        cursor: pointer;
    }
    
    .btn-primary:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(26, 71, 42, 0.3);
    }
    
    /* Stats cards */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #1a472a;
    }
    
    .stat-label {
        font-size: 0.8rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Dashboard link card */
    .dashboard-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    .dashboard-card:hover {
        border-color: #1a472a;
        box-shadow: 0 4px 12px rgba(26, 71, 42, 0.15);
    }
    
    /* Welcome section */
    .welcome-section {
        background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 50%, #3d6b4d 100%);
        border-radius: 16px;
        padding: 2.5rem;
        color: white;
        margin-bottom: 2rem;
    }
    
    .welcome-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .welcome-text {
        opacity: 0.9;
        font-size: 0.95rem;
    }
    
    /* Links */
    a {
        color: #1a472a;
        text-decoration: none;
    }
    
    a:hover {
        text-decoration: underline;
    }
    
    /* Streamlit overrides */
    .stButton > button {
        background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2d5a3d 0%, #3d6b4d 100%);
    }
</style>
""", unsafe_allow_html=True)

# Dados de exemplo (depois você pode conectar a um banco de dados ou API)
RELEASE_NOTES = [
    {
        "title": "Bem Agro - O que há de novo - 1.0",
        "platform": "Power BI",
        "status": "Publicado",
        "date": "2 de dezembro de 2025",
        "summary": "Atualizações incluem ajustes visuais como alteração de nome de página e inversão de títulos nos inputs de falhas, além da inclusão de novos visuais como tipagem de folhagem e overview de percentual de infestação. Correções foram feitas em valores divergentes e cálculos de representatividade.",
        "url": "https://app.powerbi.com/rep...2a9a48"
    }
]

DASHBOARDS = [
    {
        "name": "Dashboard de Monitoramento",
        "description": "Acompanhamento em tempo real das métricas de campo",
        "url": "https://app.powerbi.com/...",
        "icon": "📊"
    },
    {
        "name": "Relatório de Infestação",
        "description": "Análise detalhada de percentuais de infestação por área",
        "url": "https://app.powerbi.com/...",
        "icon": "🌿"
    },
    {
        "name": "Painel de Produtividade",
        "description": "Indicadores de desempenho e produtividade agrícola",
        "url": "https://app.powerbi.com/...",
        "icon": "📈"
    }
]

# Inicializar estado da página
if 'page' not in st.session_state:
    st.session_state.page = 'home'

# Função para mudar página
def change_page(page):
    st.session_state.page = page

# Sidebar com navegação
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="logo-container">
        <div class="logo-text">🌱 Bem Agro</div>
        <div class="logo-subtitle">Portal do Cliente</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu de navegação
    st.markdown("### Navegação")
    
    if st.button("🏠  Início", use_container_width=True, key="btn_home"):
        st.session_state.page = 'home'
    
    if st.button("📋  Release Notes", use_container_width=True, key="btn_releases"):
        st.session_state.page = 'releases'
    
    if st.button("📊  Dashboards", use_container_width=True, key="btn_dashboards"):
        st.session_state.page = 'dashboards'
    
    if st.button("📚  Documentação", use_container_width=True, key="btn_docs"):
        st.session_state.page = 'docs'
    
    if st.button("💬  Suporte", use_container_width=True, key="btn_support"):
        st.session_state.page = 'support'
    
    # Footer da sidebar
    st.markdown("---")
    st.markdown(f"<small style='opacity: 0.7'>© 2025 Bem Agro</small>", unsafe_allow_html=True)

# Conteúdo principal baseado na página selecionada
if st.session_state.page == 'home':
    # Página Inicial
    st.markdown("""
    <div class="welcome-section">
        <div class="welcome-title">👋 Bem-vindo ao Portal Bem Agro</div>
        <div class="welcome-text">Acompanhe as atualizações, acesse seus dashboards e encontre toda a documentação em um só lugar.</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">3</div>
            <div class="stat-label">Dashboards</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">1</div>
            <div class="stat-label">Atualizações</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">5</div>
            <div class="stat-label">Documentos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">24/7</div>
            <div class="stat-label">Suporte</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Seções rápidas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Últimas Atualizações")
        for note in RELEASE_NOTES[:2]:
            st.markdown(f"""
            <div class="card">
                <div class="card-header">
                    <div>
                        <p class="card-title">{note['title']}</p>
                        <span class="badge badge-powerbi">{note['platform']}</span>
                    </div>
                    <span class="card-date">{note['date']}</span>
                </div>
                <p class="card-description">{note['summary'][:150]}...</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Acesso Rápido")
        for dash in DASHBOARDS[:3]:
            st.markdown(f"""
            <div class="dashboard-card">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{dash['icon']}</div>
                <div style="font-weight: 600; color: #1f2937;">{dash['name']}</div>
                <div style="font-size: 0.85rem; color: #6b7280;">{dash['description']}</div>
            </div>
            <br>
            """, unsafe_allow_html=True)

elif st.session_state.page == 'releases':
    # Página de Release Notes
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📋 Release Notes</h1>
        <p class="page-description">Acompanhe todas as atualizações e melhorias dos seus dashboards</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        platform_filter = st.selectbox("Plataforma", ["Todas", "Power BI", "Excel", "Outro"])
    with col2:
        status_filter = st.selectbox("Status", ["Todos", "Publicado", "Em desenvolvimento"])
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Lista de releases
    for note in RELEASE_NOTES:
        status_class = "badge-published" if note['status'] == "Publicado" else "badge-draft"
        st.markdown(f"""
        <div class="card">
            <div class="card-header">
                <div>
                    <p class="card-title">{note['title']}</p>
                    <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                        <span class="badge badge-powerbi">{note['platform']}</span>
                        <span class="badge {status_class}">{note['status']}</span>
                    </div>
                </div>
                <span class="card-date">📅 {note['date']}</span>
            </div>
            <p class="card-description">{note['summary']}</p>
            <div style="margin-top: 1rem;">
                <a href="{note['url']}" target="_blank" class="btn-primary">
                    🔗 Acessar Dashboard
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == 'dashboards':
    # Página de Dashboards
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📊 Dashboards</h1>
        <p class="page-description">Acesse todos os seus relatórios e painéis de análise</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Grid de dashboards
    cols = st.columns(3)
    for i, dash in enumerate(DASHBOARDS):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="card" style="text-align: center; padding: 2rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">{dash['icon']}</div>
                <h3 style="margin: 0 0 0.5rem 0; color: #1f2937;">{dash['name']}</h3>
                <p style="color: #6b7280; font-size: 0.9rem; margin-bottom: 1.5rem;">{dash['description']}</p>
                <a href="{dash['url']}" target="_blank" style="
                    background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%);
                    color: white;
                    padding: 0.625rem 1.25rem;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 0.875rem;
                    text-decoration: none;
                ">Acessar →</a>
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.page == 'docs':
    # Página de Documentação
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">📚 Documentação</h1>
        <p class="page-description">Guias, tutoriais e materiais de apoio</p>
    </div>
    """, unsafe_allow_html=True)
    
    docs = [
        {"title": "Guia de Início Rápido", "desc": "Aprenda a navegar pelos dashboards", "icon": "🚀"},
        {"title": "Manual do Usuário", "desc": "Documentação completa das funcionalidades", "icon": "📖"},
        {"title": "FAQ - Perguntas Frequentes", "desc": "Respostas para dúvidas comuns", "icon": "❓"},
        {"title": "Glossário de Termos", "desc": "Definições e terminologias utilizadas", "icon": "📝"},
        {"title": "Boas Práticas", "desc": "Dicas para melhor aproveitamento", "icon": "💡"},
    ]
    
    for doc in docs:
        st.markdown(f"""
        <div class="card" style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2rem;">{doc['icon']}</div>
            <div>
                <h4 style="margin: 0; color: #1f2937;">{doc['title']}</h4>
                <p style="margin: 0; color: #6b7280; font-size: 0.9rem;">{doc['desc']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.page == 'support':
    # Página de Suporte
    st.markdown("""
    <div class="page-header">
        <h1 class="page-title">💬 Suporte</h1>
        <p class="page-description">Estamos aqui para ajudar</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="margin-top: 0;">📧 Entre em Contato</h3>
            <p style="color: #6b7280;">Envie uma mensagem para nossa equipe de suporte.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("support_form"):
            name = st.text_input("Nome")
            email = st.text_input("E-mail")
            subject = st.selectbox("Assunto", ["Dúvida técnica", "Sugestão", "Problema", "Outro"])
            message = st.text_area("Mensagem")
            submitted = st.form_submit_button("Enviar Mensagem")
            
            if submitted:
                st.success("✅ Mensagem enviada com sucesso! Retornaremos em breve.")
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="margin-top: 0;">📞 Outros Canais</h3>
            <div style="margin: 1rem 0;">
                <strong>E-mail:</strong><br>
                suporte@bemagro.com.br
            </div>
            <div style="margin: 1rem 0;">
                <strong>WhatsApp:</strong><br>
                (11) 99999-9999
            </div>
            <div style="margin: 1rem 0;">
                <strong>Horário de Atendimento:</strong><br>
                Segunda a Sexta, 8h às 18h
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card" style="background: #f0fdf4; border-color: #86efac;">
            <h4 style="margin-top: 0; color: #166534;">💡 Dica</h4>
            <p style="color: #166534; margin-bottom: 0;">Confira nossa seção de <strong>Documentação</strong> para respostas rápidas às dúvidas mais comuns.</p>
        </div>
        """, unsafe_allow_html=True)