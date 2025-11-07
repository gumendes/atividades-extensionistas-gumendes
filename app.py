import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Praça Zumbi dos Palmares",
    page_icon="🏃‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .risk-high {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #f44336;
        margin: 0.5rem 0;
    }
    .risk-medium {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #ff9800;
        margin: 0.5rem 0;
    }
    .risk-low {
        background-color: #e8f5e9;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #4caf50;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
@st.cache_data
def carregar_dados():
    """Carrega todos os dados necessários"""
    try:
        # Dados históricos
        df_historico = pd.read_csv('dados_praça_set-out.csv', sep=';', encoding='utf-8')
        df_historico.columns = df_historico.columns.str.strip()
        df_historico = df_historico.rename(columns={'Hor rio': 'horario', 'Nome': 'nome'})
        df_historico['nome'] = df_historico['nome'].replace({
            'L£cia': 'Lúcia', 'J£lia': 'Júlia', 'F tima': 'Fátima'
        })
        df_historico['data'] = pd.to_datetime(df_historico['data'])
        df_historico['presente'] = df_historico['presente'].astype(bool)
        
        # Cadastro de alunas
        df_alunas = df_historico[['id_aluna', 'nome', 'idade', 'sexo']].drop_duplicates()
        
        # Previsões (se existir)
        try:
            df_previsoes = pd.read_csv('previsoes_outubro_rf.csv', encoding='utf-8')
            df_previsoes['data'] = pd.to_datetime(df_previsoes['data'])
        except:
            df_previsoes = None
        
        return df_historico, df_alunas, df_previsoes
    
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None

def calcular_metricas(df_historico, df_alunas):
    """Calcula métricas por aluna"""
    metricas = []
    
    for _, aluna in df_alunas.iterrows():
        dados_aluna = df_historico[df_historico['id_aluna'] == aluna['id_aluna']].sort_values('data')
        
        if len(dados_aluna) == 0:
            continue
        
        total_registros = len(dados_aluna)
        total_presencas = dados_aluna['presente'].sum()
        taxa_presenca = (total_presencas / total_registros) * 100
        
        ultimos_7 = dados_aluna.tail(7)
        ultimos_30 = dados_aluna.tail(30)
        
        presenca_7d = ultimos_7['presente'].sum()
        presenca_30d = ultimos_30['presente'].sum()
        taxa_7d = (ultimos_7['presente'].mean() * 100) if len(ultimos_7) > 0 else 0
        taxa_30d = (ultimos_30['presente'].mean() * 100) if len(ultimos_30) > 0 else 0
        
        sequencia = 0
        for _, row in dados_aluna.iloc[::-1].iterrows():
            if row['presente']:
                sequencia += 1
            else:
                break
        
        risco = (1 - (taxa_7d/100 * 0.7 + taxa_30d/100 * 0.3)) * 100
        risco = max(0, min(100, risco))
        
        pontos = total_presencas * 10 + sequencia * 5
        
        metricas.append({
            'id_aluna': aluna['id_aluna'],
            'nome': aluna['nome'],
            'idade': aluna['idade'],
            'total_presencas': int(total_presencas),
            'taxa_presenca': round(taxa_presenca, 1),
            'presenca_7d': int(presenca_7d),
            'taxa_7d': round(taxa_7d, 1),
            'sequencia_atual': sequencia,
            'risco_falta': round(risco, 1),
            'pontos': int(pontos)
        })
    
    return pd.DataFrame(metricas)

# Carregar dados
df_historico, df_alunas, df_previsoes = carregar_dados()

if df_historico is None:
    st.error("❌ Erro ao carregar dados. Verifique os arquivos CSV.")
    st.stop()

df_metricas = calcular_metricas(df_historico, df_alunas)

# Sidebar
with st.sidebar:
    st.markdown("### 📊 Informações do Sistema")
    st.info(f"""
    **📅 Período dos Dados:**  
    {df_historico['data'].min().strftime('%d/%m/%Y')} a {df_historico['data'].max().strftime('%d/%m/%Y')}
    
    **👥 Total de Alunas:** {len(df_alunas)}
    
    **✅ Taxa de Presença:** {df_historico['presente'].mean()*100:.1f}%
    """)

# Header
st.markdown('<h1 class="main-header">🏃‍♀️ Praça Zumbi dos Palmares</h1>', unsafe_allow_html=True)

# Tabs
tab_prof, tab_gamif = st.tabs(["👩‍🏫 Painel da Professora", "🏆 Gamificação"])

# TAB 1: Painel da Professora
with tab_prof:
    st.header("📊 Painel de Gestão")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total de Alunas", len(df_alunas))
    
    with col2:
        taxa_geral = df_historico['presente'].mean() * 100
        st.metric("✅ Taxa de Presença", f"{taxa_geral:.1f}%")
    
    with col3:
        alto_risco = len(df_metricas[df_metricas['risco_falta'] > 60])
        st.metric("⚠️ Alto Risco", alto_risco)
    
    with col4:
        media_seq = df_metricas['sequencia_atual'].mean()
        st.metric("🔥 Sequência Média", f"{media_seq:.1f}")
    
    st.markdown("---")
    
    # Filtros
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        filtro_risco = st.selectbox(
            "Nível de Risco",
            ["Todos", "Alto (>60%)", "Médio (30-60%)", "Baixo (<30%)"]
        )
    
    with col_f2:
        limite = st.slider("Mostrar quantas?", 5, 20, 10)
    
    # Aplicar filtros
    df_mostrar = df_metricas.copy()
    
    if filtro_risco == "Alto (>60%)":
        df_mostrar = df_mostrar[df_mostrar['risco_falta'] > 60]
    elif filtro_risco == "Médio (30-60%)":
        df_mostrar = df_mostrar[(df_mostrar['risco_falta'] >= 30) & (df_mostrar['risco_falta'] <= 60)]
    elif filtro_risco == "Baixo (<30%)":
        df_mostrar = df_mostrar[df_mostrar['risco_falta'] < 30]
    
    df_mostrar = df_mostrar.sort_values('risco_falta', ascending=False).head(limite)
    
    st.subheader("🎯 Lista de Alunas")
    
    for idx, row in df_mostrar.iterrows():
        risco = row['risco_falta']
        
        if risco > 60:
            classe = "risk-high"
            emoji = "🔴"
            nivel = "ALTO"
        elif risco > 30:
            classe = "risk-medium"
            emoji = "🟡"
            nivel = "MÉDIO"
        else:
            classe = "risk-low"
            emoji = "🟢"
            nivel = "BAIXO"
        
        with st.container():
            st.markdown(f'<div class="{classe}">', unsafe_allow_html=True)
            
            col_a, col_b = st.columns([3, 2])
            
            with col_a:
                st.markdown(f"### {emoji} {row['nome']}")
                st.write(f"**Risco:** {risco:.1f}% ({nivel})")
            
            with col_b:
                st.write(f"**Presença 7d:** {row['presenca_7d']}/7")
                st.write(f"**Sequência:** {row['sequencia_atual']} 🔥")
            
            if risco > 40:
                with st.expander("📱 Mensagem de incentivo"):
                    mensagem = f"""Olá {row['nome']}! 😊
                    
Sentimos sua falta nas aulas! 💙
A turma está te esperando!

Contamos com você! 💪
- Professora"""
                    st.text_area("", mensagem, height=150, key=f"msg_{row['id_aluna']}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráficos
    st.subheader("📈 Análises")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        exercicio_stats = df_historico.groupby('tipo_exercicio')['presente'].mean() * 100
        fig1 = px.bar(
            x=exercicio_stats.index,
            y=exercicio_stats.values,
            title='Taxa por Tipo de Exercício',
            color=exercicio_stats.values,
            color_continuous_scale='Blues'
        )
        fig1.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_g2:
        evolucao = df_historico.groupby(df_historico['data'].dt.date)['presente'].mean() * 100
        fig2 = px.line(
            x=evolucao.index,
            y=evolucao.values,
            title='Evolução da Presença',
            markers=True
        )
        fig2.update_traces(line_color='#1f77b4', line_width=3)
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

# TAB 2: Gamificação
with tab_gamif:
    st.header("🏆 Gamificação")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        melhor_seq = df_metricas['sequencia_atual'].max()
        st.metric("🔥 Melhor Sequência", f"{melhor_seq} dias")
    
    with col2:
        total_pts = df_metricas['pontos'].sum()
        st.metric("⭐ Pontos Totais", f"{total_pts:,}")
    
    with col3:
        campea = df_metricas.sort_values('pontos', ascending=False).iloc[0]['nome']
        st.metric("👑 Líder", campea)
    
    st.markdown("---")
    st.subheader("👑 Ranking TOP 10")
    
    df_ranking = df_metricas.sort_values('pontos', ascending=False).head(10).reset_index(drop=True)
    
    for idx, row in df_ranking.iterrows():
        pos = idx + 1
        
        if pos == 1:
            emoji = "🥇"
        elif pos == 2:
            emoji = "🥈"
        elif pos == 3:
            emoji = "🥉"
        else:
            emoji = f"{pos}º"
        
        col_r1, col_r2, col_r3 = st.columns([1, 3, 2])
        
        with col_r1:
            st.markdown(f"### {emoji}")
        
        with col_r2:
            st.markdown(f"### {row['nome']}")
        
        with col_r3:
            st.metric("Pontos", f"{row['pontos']}")
        
        st.markdown("---")
    
    # Gráfico ranking
    fig_rank = px.bar(
        df_ranking,
        x='pontos',
        y='nome',
        orientation='h',
        title='Ranking de Pontos',
        color='pontos',
        color_continuous_scale='Viridis'
    )
    fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
    st.plotly_chart(fig_rank, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📊 Evolução Individual")
    
    aluna_sel = st.selectbox("Selecione uma aluna:", df_metricas['nome'].sort_values().tolist())
    
    id_aluna = df_metricas[df_metricas['nome'] == aluna_sel]['id_aluna'].values[0]
    dados_aluna = df_historico[df_historico['id_aluna'] == id_aluna].sort_values('data')
    dados_aluna_viz = dados_aluna.copy()
    dados_aluna_viz['presenca_acumulada'] = dados_aluna_viz['presente'].cumsum()
    
    fig_ev = go.Figure()
    fig_ev.add_trace(go.Scatter(
        x=dados_aluna_viz['data'],
        y=dados_aluna_viz['presenca_acumulada'],
        mode='lines+markers',
        line=dict(color='#2ecc71', width=3),
        fill='tozeroy'
    ))
    
    fig_ev.update_layout(
        title=f'Evolução de {aluna_sel}',
        xaxis_title='Data',
        yaxis_title='Presenças Acumuladas',
        height=400
    )
    
    st.plotly_chart(fig_ev, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #666;'>
    <p><strong>Praça Zumbi dos Palmares - Parque América, São Paulo</strong></p>
    <p><em>TCC - Ciência de Dados</em></p>
</div>
""", unsafe_allow_html=True)
