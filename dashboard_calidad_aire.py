#!/usr/bin/env python3
"""
Dashboard de Calidad del Aire en Tiempo Real + Machine Learning
Visualización interactiva + Predicciones de AQI
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
from datetime import datetime, timedelta
import time
import joblib
import numpy as np
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Calidad del Aire - USA + ML",
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
    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
    }
    .model-comparison {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
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
# CARGAR MODELOS ML
# ============================================================================

@st.cache_resource
def load_ml_models():
    """Carga los modelos de Machine Learning"""
    models = {}
    
    try:
        # Intentar cargar modelo 1 (RandomForest)
        if Path("modelo1_aqi.pkl").exists():
            models['modelo1'] = joblib.load("modelo1_aqi.pkl")
            models['modelo1_name'] = "Random Forest"
        else:
            models['modelo1'] = None
            
        # Intentar cargar modelo 2 (XGBoost)
        if Path("modelo2_aqi.pkl").exists():
            models['modelo2'] = joblib.load("modelo2_aqi.pkl")
            models['modelo2_name'] = "XGBoost + IsolationForest"
        else:
            models['modelo2'] = None
            
    except Exception as e:
        st.error(f"Error cargando modelos: {e}")
        models['modelo1'] = None
        models['modelo2'] = None
    
    return models

# ============================================================================
# FUNCIONES DE DATOS
# ============================================================================

@st.cache_resource
def get_connection():
    """Crea y cachea conexión a la base de datos"""
    return psycopg2.connect(**DB_CONFIG)

@st.cache_data(ttl=60)
def fetch_latest_readings(hours=24):
    """Obtiene lecturas recientes"""
    conn = get_connection()
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

@st.cache_data(ttl=60)
def fetch_summary_by_state(hours=24):
    """Resumen por estado"""
    conn = get_connection()
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

@st.cache_data(ttl=60)
def fetch_summary_by_contaminante(hours=24):
    """Resumen por contaminante"""
    conn = get_connection()
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

@st.cache_data(ttl=60)
def fetch_time_series(contaminante=None, hours=24):
    """Series temporales de AQI"""
    conn = get_connection()
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

def get_unique_values():
    """Obtiene valores únicos para los selectores de predicción"""
    conn = get_connection()
    
    # Ciudades
    ciudades = pd.read_sql("SELECT DISTINCT ciudad FROM mediciones ORDER BY ciudad", conn)['ciudad'].tolist()
    
    # Estados
    estados = pd.read_sql("SELECT DISTINCT estado FROM mediciones ORDER BY estado", conn)['estado'].tolist()
    
    # Contaminantes
    contaminantes = pd.read_sql("SELECT DISTINCT contaminante FROM mediciones ORDER BY contaminante", conn)['contaminante'].tolist()
    
    # Categorías
    categorias = pd.read_sql("SELECT DISTINCT categoria FROM mediciones ORDER BY categoria", conn)['categoria'].tolist()
    
    return ciudades, estados, contaminantes, categorias

# ============================================================================
# FUNCIÓN DE PREDICCIÓN
# ============================================================================

def predict_aqi(models, ciudad, estado, contaminante, latitud, longitud, fecha=None, categoria=None):
    """Realiza predicción con ambos modelos"""
    
    # Preparar datos para modelo 1 (solo las columnas que necesita)
    data_modelo1 = pd.DataFrame({
        'ciudad': [ciudad],
        'estado': [estado],
        'contaminante': [contaminante],
        'latitud': [latitud],
        'longitud': [longitud]
    })
    
    # Preparar datos para modelo 2 (incluye fecha y categoria)
    data_modelo2 = pd.DataFrame({
        'ciudad': [ciudad],
        'estado': [estado],
        'contaminante': [contaminante],
        'latitud': [latitud],
        'longitud': [longitud],
        'categoria': [categoria if categoria else 'Good'],
        'fecha': [fecha if fecha else datetime.now()]
    })
    
    predictions = {}
    
    # Predicción con modelo 1
    if models['modelo1'] is not None:
        try:
            pred1 = models['modelo1'].predict(data_modelo1)[0]
            predictions['modelo1'] = pred1
        except Exception as e:
            predictions['modelo1'] = None
            predictions['modelo1_error'] = str(e)
    
    # Predicción con modelo 2
    if models['modelo2'] is not None:
        try:
            pred2 = models['modelo2'].predict(data_modelo2)[0]
            predictions['modelo2'] = pred2
        except Exception as e:
            predictions['modelo2'] = None
            predictions['modelo2_error'] = str(e)
    
    return predictions

# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================

# Cargar modelos
models = load_ml_models()

# Header
st.markdown('<h1 class="main-header">🌍 Calidad del Aire - USA + 🤖 ML</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Monitoreo en Tiempo Real + Predicciones con Machine Learning</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selector de pestaña principal
    tab_selection = st.radio(
        "Seleccionar Vista",
        ["📊 Dashboard", "🤖 Predicciones ML"],
        index=0
    )
    
    st.markdown("---")
    
    if tab_selection == "📊 Dashboard":
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
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
        
        df_all = fetch_latest_readings(hours=48)
        
        estados_disponibles = ["Todos"] + sorted(df_all['estado'].dropna().unique().tolist())
        estado_seleccionado = st.selectbox("Estado", estados_disponibles)
        
        contaminantes_disponibles = ["Todos"] + sorted(df_all['contaminante'].dropna().unique().tolist())
        contaminante_seleccionado = st.selectbox("Contaminante", contaminantes_disponibles)
    
    else:
        st.subheader("🤖 Modelos Disponibles")
        if models['modelo1'] is not None:
            st.success(f"✅ {models['modelo1_name']}")
        else:
            st.error("❌ Modelo 1 no cargado")
            
        if models['modelo2'] is not None:
            st.success(f"✅ {models['modelo2_name']}")
        else:
            st.error("❌ Modelo 2 no cargado")
    
    st.markdown("---")
    st.info(f"**Última actualización:** {datetime.now().strftime('%H:%M:%S')}")
    st.caption("Datos de EPA AirNow")

# ============================================================================
# PESTAÑA: DASHBOARD
# ============================================================================

if tab_selection == "📊 Dashboard":
    
    placeholder = st.empty()
    
    while True:
        with placeholder.container():
            # Obtener datos
            df = fetch_latest_readings(hours=time_window)
            
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
            
            # MÉTRICAS PRINCIPALES
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
            
            # MAPA Y DISTRIBUCIÓN
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("🗺️ Mapa de Calidad del Aire")
                
                df_map = df_filtered.sort_values('fecha').groupby('ciudad').last().reset_index()
                
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
                    center={"lat": 39.8283, "lon": -98.5795},
                    range_color=[0, 150]
                )
                
                fig_map.update_layout(
                    mapbox_style="open-street-map",
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                
                st.plotly_chart(fig_map, use_container_width=True)
            
            with col2:
                st.subheader("📊 Distribución de AQI")
                
                fig_hist = px.histogram(
                    df_filtered,
                    x='aqi',
                    nbins=30,
                    color_discrete_sequence=['#3498db']
                )
                
                fig_hist.update_layout(
                    height=250,
                    showlegend=False,
                    xaxis_title="AQI",
                    yaxis_title="Frecuencia"
                )
                
                st.plotly_chart(fig_hist, use_container_width=True)
                
                st.markdown("**Por Categoría:**")
                categoria_counts = df_filtered['categoria'].value_counts()
                
                for cat, count in categoria_counts.items():
                    pct = (count / len(df_filtered) * 100)
                    st.write(f"{cat}: {count} ({pct:.1f}%)")
            
            # RANKINGS
            st.markdown("---")
            st.subheader("🏆 Rankings por Estado")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Estados con Mayor AQI Promedio**")
                summary_state = fetch_summary_by_state(hours=time_window)
                
                if not summary_state.empty:
                    fig_state = px.bar(
                        summary_state.head(10),
                        x='estado',
                        y='aqi_promedio',
                        color='aqi_promedio',
                        color_continuous_scale='RdYlGn_r'
                    )
                    
                    fig_state.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_state, use_container_width=True)
            
            with col2:
                st.markdown("**Distribución por Contaminante**")
                summary_cont = fetch_summary_by_contaminante(hours=time_window)
                
                if not summary_cont.empty:
                    fig_cont = px.bar(
                        summary_cont,
                        x='contaminante',
                        y='total_lecturas',
                        color='aqi_promedio',
                        color_continuous_scale='RdYlGn_r'
                    )
                    
                    fig_cont.update_layout(height=350, showlegend=False)
                    st.plotly_chart(fig_cont, use_container_width=True)
            
            # SERIES TEMPORALES
            st.markdown("---")
            st.subheader("📈 Tendencias Temporales")
            
            selected_cont_chart = st.selectbox(
                "Seleccionar contaminante para el gráfico:",
                ["Todos"] + sorted(df_filtered['contaminante'].unique().tolist()),
                key="cont_chart"
            )
            
            ts_cont = None if selected_cont_chart == "Todos" else selected_cont_chart
            df_ts = fetch_time_series(contaminante=ts_cont, hours=time_window)
            
            if not df_ts.empty:
                fig_ts = px.line(
                    df_ts,
                    x='hora',
                    y='aqi_promedio',
                    color='contaminante',
                    markers=True
                )
                
                fig_ts.add_hline(y=50, line_dash="dash", line_color="green")
                fig_ts.add_hline(y=100, line_dash="dash", line_color="yellow")
                fig_ts.add_hline(y=150, line_dash="dash", line_color="orange")
                
                fig_ts.update_layout(height=400)
                st.plotly_chart(fig_ts, use_container_width=True)
            
            # TABLA
            st.markdown("---")
            st.subheader("📋 Lecturas Recientes")
            
            df_table = df_filtered[['fecha', 'ciudad', 'estado', 'contaminante', 'aqi', 'categoria']].head(20)
            df_table['fecha'] = pd.to_datetime(df_table['fecha']).dt.strftime('%Y-%m-%d %H:%M')
            df_table['Estado'] = df_table['aqi'].apply(lambda x: get_aqi_category_info(x)[2])
            
            st.dataframe(
                df_table,
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            st.caption(f"Dashboard actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not auto_refresh:
            break
        
        time.sleep(refresh_interval)
        st.rerun()

# ============================================================================
# PESTAÑA: PREDICCIONES ML
# ============================================================================

else:  # tab_selection == "🤖 Predicciones ML"
    
    st.header("🤖 Predicción de AQI con Machine Learning")
    
    # Verificar que al menos un modelo esté cargado
    if models['modelo1'] is None and models['modelo2'] is None:
        st.error("❌ No se pudieron cargar los modelos de ML")
        st.info("""
        **Para habilitar las predicciones:**
        1. Asegúrate de tener los archivos `modelo1_aqi.pkl` y `modelo2_aqi.pkl`
        2. Súbelos a tu repositorio de GitHub en la raíz del proyecto
        3. Haz commit y push
        4. Streamlit Cloud los cargará automáticamente
        """)
        st.stop()
    
    # Obtener valores únicos para los selectores
    ciudades, estados, contaminantes, categorias = get_unique_values()
    
    st.markdown("### 📝 Ingresa los datos para la predicción")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pred_ciudad = st.selectbox("Ciudad", ciudades, key="pred_ciudad")
        pred_estado = st.selectbox("Estado", estados, key="pred_estado")
        pred_contaminante = st.selectbox("Contaminante", contaminantes, key="pred_contaminante")
    
    with col2:
        pred_latitud = st.number_input("Latitud", min_value=20.0, max_value=70.0, value=40.0, step=0.1, key="pred_lat")
        pred_longitud = st.number_input("Longitud", min_value=-180.0, max_value=-60.0, value=-100.0, step=0.1, key="pred_lon")
        
        # Solo para modelo 2
        if models['modelo2'] is not None:
            pred_categoria = st.selectbox("Categoría (solo para Modelo 2)", categorias, key="pred_cat")
        else:
            pred_categoria = None
    
    # Botón de predicción
    if st.button("🔮 Predecir AQI", type="primary", use_container_width=True):
        
        with st.spinner("Realizando predicciones..."):
            predictions = predict_aqi(
                models,
                pred_ciudad,
                pred_estado,
                pred_contaminante,
                pred_latitud,
                pred_longitud,
                categoria=pred_categoria
            )
        
        # Mostrar resultados
        st.markdown("---")
        st.markdown("### 🎯 Resultados de las Predicciones")
        
        col1, col2 = st.columns(2)
        
        # Modelo 1
        with col1:
            if predictions.get('modelo1') is not None:
                pred_aqi_1 = predictions['modelo1']
                category_1, color_1, emoji_1 = get_aqi_category_info(pred_aqi_1)
                
                st.markdown(f"""
                <div class="prediction-card">
                    <h3>🌲 {models['modelo1_name']}</h3>
                    <h1 style="font-size: 3rem; margin: 1rem 0;">{emoji_1} {pred_aqi_1:.1f}</h1>
                    <p style="font-size: 1.2rem;">{category_1}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"❌ Error en Modelo 1: {predictions.get('modelo1_error', 'Desconocido')}")
        
        # Modelo 2
        with col2:
            if predictions.get('modelo2') is not None:
                pred_aqi_2 = predictions['modelo2']
                category_2, color_2, emoji_2 = get_aqi_category_info(pred_aqi_2)
                
                st.markdown(f"""
                <div class="prediction-card">
                    <h3>⚡ {models['modelo2_name']}</h3>
                    <h1 style="font-size: 3rem; margin: 1rem 0;">{emoji_2} {pred_aqi_2:.1f}</h1>
                    <p style="font-size: 1.2rem;">{category_2}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"❌ Error en Modelo 2: {predictions.get('modelo2_error', 'Desconocido')}")
        
        # Comparación
        if predictions.get('modelo1') is not None and predictions.get('modelo2') is not None:
            st.markdown("---")
            st.markdown("### 📊 Comparación de Modelos")
            
            diff = abs(predictions['modelo1'] - predictions['modelo2'])
            avg_pred = (predictions['modelo1'] + predictions['modelo2']) / 2
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Predicción Promedio", f"{avg_pred:.1f}")
            
            with col2:
                st.metric("Diferencia entre Modelos", f"{diff:.1f}")
            
            with col3:
                agreement = "Alta" if diff < 10 else ("Media" if diff < 20 else "Baja")
                st.metric("Concordancia", agreement)
            
            # Gráfico de comparación
            fig_compare = go.Figure()
            
            fig_compare.add_trace(go.Bar(
                name=models['modelo1_name'],
                x=[models['modelo1_name']],
                y=[predictions['modelo1']],
                marker_color='#667eea'
            ))
            
            fig_compare.add_trace(go.Bar(
                name=models['modelo2_name'],
                x=[models['modelo2_name']],
                y=[predictions['modelo2']],
                marker_color='#764ba2'
            ))
            
            fig_compare.update_layout(
                title="Predicciones por Modelo",
                yaxis_title="AQI Predicho",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_compare, use_container_width=True)
    
    # Información sobre los modelos
    st.markdown("---")
    st.markdown("### 📚 Información de los Modelos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if models['modelo1'] is not None:
            st.markdown(f"""
            <div class="model-comparison">
                <h4>🌲 {models['modelo1_name']}</h4>
                <p><strong>Algoritmo:</strong> Random Forest Regressor</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>Ciudad (categórica)</li>
                    <li>Estado (categórica)</li>
                    <li>Contaminante (categórica)</li>
                    <li>Latitud (numérica)</li>
                    <li>Longitud (numérica)</li>
                </ul>
                <p><strong>Preprocesamiento:</strong> OneHotEncoder + StandardScaler</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if models['modelo2'] is not None:
            st.markdown(f"""
            <div class="model-comparison">
                <h4>⚡ {models['modelo2_name']}</h4>
                <p><strong>Algoritmo:</strong> XGBoost Regressor</p>
                <p><strong>Features:</strong></p>
                <ul>
                    <li>Ciudad (categórica)</li>
                    <li>Estado (categórica)</li>
                    <li>Contaminante (categórica)</li>
                    <li>Categoría (categórica)</li>
                    <li>Fecha (categórica)</li>
                    <li>Latitud (numérica)</li>
                    <li>Longitud (numérica)</li>
                </ul>
                <p><strong>Preprocesamiento:</strong> IsolationForest + OneHotEncoder + StandardScaler</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Sección de predicción batch
    st.markdown("---")
    st.markdown("### 📊 Predicción por Lote (Batch)")
    
    st.info("💡 Próximamente: Carga un CSV con múltiples ubicaciones y obtén predicciones masivas")
