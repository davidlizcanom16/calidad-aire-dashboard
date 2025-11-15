#!/usr/bin/env python3
"""
Dashboard de Calidad del Aire en Tiempo Real
Visualización interactiva para la tabla mediciones
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
from datetime import datetime, timedelta
import time

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Calidad del Aire - USA",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================

# Leer credenciales de secrets (en Streamlit Cloud) o usar valores por defecto (local)
if 'database' in st.secrets:
    # En Streamlit Cloud - usar secrets
    DB_CONFIG = {
        'host': st.secrets["database"]["host"],
        'port': st.secrets["database"]["port"],
        'database': st.secrets["database"]["dbname"],
        'user': st.secrets["database"]["user"],
        'password': st.secrets["database"]["password"],
        'sslmode': st.secrets["database"]["sslmode"]
    }
else:
    # Desarrollo local - usar credenciales directamente
    DB_CONFIG = {
        'host': 'big-data-analytics-server.postgres.database.azure.com',
        'port': 5432,
        'database': 'calidad_aire',
        'user': 'postgres',
        'password': 'Herrera123',
        'sslmode': 'require'
    }

# ============================================================================
# FUNCIONES DE DATOS
# ============================================================================

@st.cache_resource
def get_connection():
    """Crea y cachea conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

def fetch_latest_readings(conn, hours=24):
    """Obtiene lecturas recientes"""
    query = f"""
    SELECT 
        id,
        fecha,
        ciudad,
        estado,
        latitud,
        longitud,
        contaminante,
        aqi,
        categoria
    FROM mediciones
    WHERE fecha > NOW() - INTERVAL '{hours} hours'
    ORDER BY fecha DESC
    """
    return pd.read_sql(query, conn)

def fetch_summary_by_state(conn, hours=24):
    """Resumen por estado"""
    query = f"""
    SELECT 
        estado,
        COUNT(*) as total_lecturas,
        AVG(aqi) as aqi_promedio,
        MAX(aqi) as aqi_maximo,
        MIN(aqi) as aqi_minimo
    FROM mediciones
    WHERE fecha > NOW() - INTERVAL '{hours} hours'
    AND aqi IS NOT NULL
    GROUP BY estado
    ORDER BY aqi_promedio DESC
    """
    return pd.read_sql(query, conn)

def fetch_summary_by_contaminante(conn, hours=24):
    """Resumen por contaminante"""
    query = f"""
    SELECT 
        contaminante,
        COUNT(*) as total_lecturas,
        AVG(aqi) as aqi_promedio,
        MAX(aqi) as aqi_maximo
    FROM mediciones
    WHERE fecha > NOW() - INTERVAL '{hours} hours'
    AND aqi IS NOT NULL
    GROUP BY contaminante
    ORDER BY contaminante
    """
    return pd.read_sql(query, conn)

def fetch_time_series(conn, contaminante=None, hours=24):
    """Series temporales de AQI"""
    contaminante_filter = f"AND contaminante = '{contaminante}'" if contaminante else ""
    
    query = f"""
    SELECT 
        DATE_TRUNC('hour', fecha) as hora,
        contaminante,
        AVG(aqi) as aqi_promedio,
        COUNT(*) as num_lecturas
    FROM mediciones
    WHERE fecha > NOW() - INTERVAL '{hours} hours'
    {contaminante_filter}
    GROUP BY DATE_TRUNC('hour', fecha), contaminante
    ORDER BY hora
    """
    return pd.read_sql(query, conn)

def get_aqi_category_info(aqi):
    """Retorna información de categoría AQI"""
    if pd.isna(aqi) or aqi is None:
        return "Unknown", "#808080", "⚪"
    
    if aqi <= 50:
        return "Good", "#00E400", "🟢"
    elif aqi <= 100:
        return "Moderate", "#FFFF00", "🟡"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#FF7E00", "🟠"
    elif aqi <= 200:
        return "Unhealthy", "#FF0000", "🔴"
    elif aqi <= 300:
        return "Very Unhealthy", "#8F3F97", "🟣"
    else:
        return "Hazardous", "#7E0023", "🟤"

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

# Header
st.markdown('<h1 class="main-header">🌍 Calidad del Aire - USA</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Monitoreo en Tiempo Real de Calidad del Aire</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    refresh_interval = st.slider("Intervalo de refresh (segundos)", 5, 60, 15)
    
    time_window = st.selectbox(
        "⏱️ Ventana de tiempo",
        options=[1, 3, 6, 12, 24, 48],
        index=4,
        format_func=lambda x: f"{x} hora{'s' if x > 1 else ''}"
    )
    
    st.markdown("---")
    
    # Filtros
    st.subheader("🔍 Filtros")
    
    # Obtener valores únicos para filtros
    conn = get_connection()
    df_all = fetch_latest_readings(conn, hours=48)
    
    estados_disponibles = ["Todos"] + sorted(df_all['estado'].dropna().unique().tolist())
    estado_seleccionado = st.selectbox("Estado", estados_disponibles)
    
    contaminantes_disponibles = ["Todos"] + sorted(df_all['contaminante'].dropna().unique().tolist())
    contaminante_seleccionado = st.selectbox("Contaminante", contaminantes_disponibles)
    
    st.markdown("---")
    st.info(f"**Última actualización:** {datetime.now().strftime('%H:%M:%S')}")
    st.caption("Datos de EPA AirNow")

# Contenedor principal
placeholder = st.empty()

# Loop principal
iteration = 0
while True:
    iteration += 1
    
    with placeholder.container():
        # Obtener datos
        df = fetch_latest_readings(conn, hours=time_window)
        
        if df.empty:
            st.warning("⚠️ No hay datos disponibles para el período seleccionado")
            break
        
        # Aplicar filtros
        df_filtered = df.copy()
        
        if estado_seleccionado != "Todos":
            df_filtered = df_filtered[df_filtered['estado'] == estado_seleccionado]
        
        if contaminante_seleccionado != "Todos":
            df_filtered = df_filtered[df_filtered['contaminante'] == contaminante_seleccionado]
        
        if df_filtered.empty:
            st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados")
            break
        
        # ================================================================
        # SECCIÓN 1: MÉTRICAS PRINCIPALES
        # ================================================================
        st.subheader("📊 Métricas Principales")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_aqi = df_filtered['aqi'].mean()
            category, color, emoji = get_aqi_category_info(avg_aqi)
            st.metric(
                "AQI Promedio",
                f"{avg_aqi:.0f}",
                delta=f"{emoji} {category}",
                delta_color="off"
            )
        
        with col2:
            max_aqi = df_filtered['aqi'].max()
            st.metric("AQI Máximo", f"{max_aqi:.0f}")
        
        with col3:
            total_lecturas = len(df_filtered)
            st.metric("Total Lecturas", f"{total_lecturas:,}")
        
        with col4:
            ciudades = df_filtered['ciudad'].nunique()
            st.metric("Ciudades", ciudades)
        
        with col5:
            estados = df_filtered['estado'].nunique()
            st.metric("Estados", estados)
        
        st.markdown("---")
        
        # ================================================================
        # SECCIÓN 2: VISUALIZACIONES PRINCIPALES
        # ================================================================
        
        # Row 1: Mapa + Distribución AQI
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🗺️ Mapa de Calidad del Aire")
            
            # Preparar datos para el mapa (última lectura por ciudad)
            df_map = df_filtered.sort_values('fecha').groupby('ciudad').last().reset_index()
            
            # Asignar colores según AQI
            df_map['color'] = df_map['aqi'].apply(lambda x: get_aqi_category_info(x)[1])
            df_map['emoji'] = df_map['aqi'].apply(lambda x: get_aqi_category_info(x)[2])
            
            fig_map = px.scatter_mapbox(
                df_map,
                lat='latitud',
                lon='longitud',
                color='aqi',
                size='aqi',
                hover_name='ciudad',
                hover_data={
                    'estado': True,
                    'aqi': True,
                    'contaminante': True,
                    'categoria': True,
                    'latitud': False,
                    'longitud': False
                },
                color_continuous_scale='RdYlGn_r',
                color_continuous_midpoint=75,
                zoom=3,
                height=500,
                center={"lat": 39.8283, "lon": -98.5795},  # Centro de USA
                range_color=[0, 150]
            )
            
            fig_map.update_layout(
                mapbox_style="open-street-map",
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
        
        with col2:
            st.subheader("📊 Distribución de AQI")
            
            # Histograma de AQI
            fig_hist = px.histogram(
                df_filtered,
                x='aqi',
                nbins=30,
                color_discrete_sequence=['#3498db'],
                labels={'aqi': 'AQI', 'count': 'Frecuencia'}
            )
            
            fig_hist.update_layout(
                height=250,
                showlegend=False,
                xaxis_title="AQI",
                yaxis_title="Frecuencia"
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Distribución por categoría
            st.markdown("**Por Categoría:**")
            categoria_counts = df_filtered['categoria'].value_counts()
            
            for cat, count in categoria_counts.items():
                pct = (count / len(df_filtered) * 100)
                st.write(f"{cat}: {count} ({pct:.1f}%)")
        
        # Row 2: Rankings por Estado
        st.markdown("---")
        st.subheader("🏆 Rankings por Estado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Estados con Mayor AQI Promedio**")
            summary_state = fetch_summary_by_state(conn, hours=time_window)
            
            if not summary_state.empty:
                fig_state = px.bar(
                    summary_state.head(10),
                    x='estado',
                    y='aqi_promedio',
                    color='aqi_promedio',
                    color_continuous_scale='RdYlGn_r',
                    labels={'aqi_promedio': 'AQI Promedio', 'estado': 'Estado'}
                )
                
                fig_state.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_state, use_container_width=True)
        
        with col2:
            st.markdown("**Distribución por Contaminante**")
            summary_cont = fetch_summary_by_contaminante(conn, hours=time_window)
            
            if not summary_cont.empty:
                fig_cont = px.bar(
                    summary_cont,
                    x='contaminante',
                    y='total_lecturas',
                    color='aqi_promedio',
                    color_continuous_scale='RdYlGn_r',
                    labels={'total_lecturas': 'Lecturas', 'contaminante': 'Contaminante'}
                )
                
                fig_cont.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig_cont, use_container_width=True)
        
        # Row 3: Series Temporales
        st.markdown("---")
        st.subheader("📈 Tendencias Temporales")
        
        # Selector de contaminante para el gráfico
        cont_options = ["Todos"] + sorted(df_filtered['contaminante'].unique().tolist())
        selected_cont_chart = st.selectbox(
            "Seleccionar contaminante para el gráfico:",
            cont_options,
            key="cont_chart"
        )
        
        # Obtener series temporales
        ts_cont = None if selected_cont_chart == "Todos" else selected_cont_chart
        df_ts = fetch_time_series(conn, contaminante=ts_cont, hours=time_window)
        
        if not df_ts.empty:
            fig_ts = px.line(
                df_ts,
                x='hora',
                y='aqi_promedio',
                color='contaminante',
                markers=True,
                labels={
                    'hora': 'Hora',
                    'aqi_promedio': 'AQI Promedio',
                    'contaminante': 'Contaminante'
                }
            )
            
            # Añadir líneas de referencia para categorías AQI
            fig_ts.add_hline(y=50, line_dash="dash", line_color="green", 
                            annotation_text="Good/Moderate")
            fig_ts.add_hline(y=100, line_dash="dash", line_color="yellow", 
                            annotation_text="Moderate/Unhealthy")
            fig_ts.add_hline(y=150, line_dash="dash", line_color="orange", 
                            annotation_text="Unhealthy")
            
            fig_ts.update_layout(height=400)
            st.plotly_chart(fig_ts, use_container_width=True)
        
        # ================================================================
        # SECCIÓN 3: TABLA DE DATOS RECIENTES
        # ================================================================
        st.markdown("---")
        st.subheader("📋 Lecturas Recientes")
        
        # Preparar tabla
        df_table = df_filtered[['fecha', 'ciudad', 'estado', 'contaminante', 'aqi', 'categoria']].head(20)
        df_table['fecha'] = pd.to_datetime(df_table['fecha']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Añadir columna con emoji de categoría
        df_table['Estado'] = df_table['aqi'].apply(lambda x: get_aqi_category_info(x)[2])
        
        st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "fecha": "Fecha/Hora",
                "ciudad": "Ciudad",
                "estado": "Estado",
                "contaminante": "Contaminante",
                "aqi": st.column_config.NumberColumn("AQI", format="%d"),
                "categoria": "Categoría",
                "Estado": "📊"
            }
        )
        
        # ================================================================
        # SECCIÓN 4: ESTADÍSTICAS DETALLADAS
        # ================================================================
        st.markdown("---")
        st.subheader("📊 Estadísticas Detalladas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Top 10 Ciudades (Mayor AQI)**")
            top_ciudades = df_filtered.groupby('ciudad')['aqi'].mean().nlargest(10)
            for ciudad, aqi in top_ciudades.items():
                emoji = get_aqi_category_info(aqi)[2]
                st.write(f"{emoji} {ciudad}: {aqi:.1f}")
        
        with col2:
            st.markdown("**Lecturas por Hora**")
            lecturas_hora = df_filtered.groupby(df_filtered['fecha'].dt.hour).size()
            for hora, count in lecturas_hora.items():
                st.write(f"Hora {hora:02d}: {count} lecturas")
        
        with col3:
            st.markdown("**Resumen por Contaminante**")
            for cont in df_filtered['contaminante'].unique():
                df_cont = df_filtered[df_filtered['contaminante'] == cont]
                avg_aqi = df_cont['aqi'].mean()
                count = len(df_cont)
                emoji = get_aqi_category_info(avg_aqi)[2]
                st.write(f"{emoji} {cont}: {avg_aqi:.1f} ({count} lecturas)")
        
        # Footer
        st.markdown("---")
        st.caption(f"Dashboard actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Iteración: {iteration} | Total registros en DB: {len(df):,}")
    
    # Control de refresh
    if not auto_refresh:
        break
    
    time.sleep(refresh_interval)
    st.rerun()
