# 🌍 Dashboard de Calidad del Aire - USA

Dashboard interactivo en tiempo real para monitoreo de calidad del aire en Estados Unidos, visualizando datos de PM2.5, O3 y PM10 de múltiples estaciones de monitoreo.

## 🚀 Demo en Vivo

**Ver dashboard:** [https://tu-app.streamlit.app](https://streamlit.io)

_(Actualiza este link después del deployment)_

## 📊 Características

### Visualizaciones
- 🗺️ **Mapa interactivo de USA** con todas las estaciones de monitoreo
- 📈 **Series temporales** de AQI con líneas de referencia EPA
- 📊 **Histogramas** de distribución de AQI
- 🏆 **Rankings** por estado y ciudad
- 📋 **Tabla de datos** en tiempo real

### Funcionalidades
- ✅ Métricas en tiempo real (AQI promedio, máximo, total lecturas)
- ✅ Filtros dinámicos por estado y contaminante
- ✅ Auto-refresh configurable (5-60 segundos)
- ✅ Categorías EPA oficiales con código de colores
- ✅ Estadísticas detalladas por ciudad y contaminante
- ✅ Ventanas de tiempo configurables (1h - 48h)

## 🎨 Capturas de Pantalla

_[Agregar screenshots después del deployment]_

## 🛠️ Tecnologías

- **Frontend:** Streamlit 1.29.0
- **Visualización:** Plotly 5.18.0
- **Base de datos:** PostgreSQL (Azure)
- **Backend:** Python 3.9+
- **Análisis de datos:** Pandas 2.1.4

## 📦 Estructura del Proyecto

```
calidad-aire-dashboard/
├── dashboard_calidad_aire.py    # Aplicación principal
├── requirements.txt              # Dependencias Python
├── .streamlit/
│   └── config.toml              # Configuración de Streamlit
├── .gitignore                   # Archivos ignorados por Git
└── README.md                    # Este archivo
```

## 🚀 Instalación y Ejecución Local

### Requisitos Previos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Acceso a internet

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/TU-USUARIO/calidad-aire-dashboard.git
   cd calidad-aire-dashboard
   ```

2. **Crear entorno virtual (opcional pero recomendado)**
   ```bash
   python -m venv venv
   
   # Activar en Windows
   venv\Scripts\activate
   
   # Activar en macOS/Linux
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   streamlit run dashboard_calidad_aire.py
   ```

5. **Abrir en el navegador**
   - La aplicación se abrirá automáticamente en `http://localhost:8501`

## 📊 Datos

### Fuente de Datos
Los datos provienen de una base de datos PostgreSQL en Azure que contiene información de estaciones de monitoreo de calidad del aire en USA.

### Contenido
- **Registros:** 7,000+ mediciones
- **Ubicaciones:** 50+ ciudades en 10+ estados
- **Contaminantes monitoreados:**
  - PM2.5 (Particulate Matter 2.5) - 38%
  - O3 (Ozone) - 33%
  - PM10 (Particulate Matter 10) - 29%
- **Rango temporal:** Datos de los últimos 2 días
- **Actualización:** Continua

### Estados Cubiertos
California (CA), Texas (TX), Arizona (AZ), North Carolina (NC), Florida (FL), Virginia (VA), Nevada (NV), Ohio (OH), Colorado (CO), Michigan (MI), y más.

## 📈 Categorías AQI (EPA)

El dashboard utiliza las categorías oficiales de la Agencia de Protección Ambiental (EPA):

| Rango AQI | Categoría | Color | Descripción |
|-----------|-----------|-------|-------------|
| 0-50 | Good | 🟢 Verde | Calidad del aire satisfactoria |
| 51-100 | Moderate | 🟡 Amarillo | Aceptable para la mayoría |
| 101-150 | Unhealthy for Sensitive Groups | 🟠 Naranja | Puede afectar a grupos sensibles |
| 151-200 | Unhealthy | 🔴 Rojo | Puede afectar a todos |
| 201-300 | Very Unhealthy | 🟣 Púrpura | Alerta de salud |
| 301+ | Hazardous | 🟤 Marrón | Emergencia de salud |

## 🎯 Casos de Uso

### Para el Público General
- Consultar calidad del aire antes de actividades al aire libre
- Identificar mejores momentos del día para ejercicio
- Comparar calidad del aire entre ciudades

### Para Investigadores
- Análisis de tendencias temporales
- Comparación de contaminantes
- Identificación de patrones geográficos

### Para Autoridades
- Monitoreo en tiempo real de múltiples estaciones
- Detección rápida de eventos de contaminación
- Datos para toma de decisiones

## 🔧 Configuración

### Variables de Entorno
Para deployment en producción, configurar secrets en Streamlit Cloud:

```toml
[database]
host = "tu-servidor.postgres.database.azure.com"
port = 5432
dbname = "calidad_aire"
user = "tu_usuario"
password = "tu_password"
sslmode = "require"
```

### Personalización
- **Colores del tema:** Editar `.streamlit/config.toml`
- **Intervalo de refresh:** Ajustar en sidebar (5-60 segundos)
- **Ventana de tiempo:** Seleccionar entre 1h y 48h
- **Filtros:** Por estado y tipo de contaminante

## 🚢 Deployment en Streamlit Cloud

1. **Fork o clonar este repositorio**
2. **Ir a [share.streamlit.io](https://share.streamlit.io)**
3. **Sign in con GitHub**
4. **New app → Seleccionar tu repositorio**
5. **Configurar secrets con credenciales de base de datos**
6. **Deploy!**

Ver guía completa en: [DEPLOYMENT_STREAMLIT_CLOUD.md](DEPLOYMENT_STREAMLIT_CLOUD.md)

## 📝 Licencia

MIT License

Copyright (c) 2025 [Tu Nombre]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 👥 Autor

**Tu Nombre**
- GitHub: [@tu-usuario](https://github.com/tu-usuario)
- LinkedIn: [Tu LinkedIn](https://linkedin.com/in/tu-perfil)
- Email: tu.email@ejemplo.com

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea tu Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al Branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📚 Recursos

- [Documentación de Streamlit](https://docs.streamlit.io)
- [Plotly Python](https://plotly.com/python/)
- [EPA AQI Guide](https://www.airnow.gov/aqi/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## ⭐ Reconocimientos

- Datos de calidad del aire cortesía de [EPA AirNow](https://www.airnow.gov)
- Built with [Streamlit](https://streamlit.io)
- Visualizaciones con [Plotly](https://plotly.com)

---

**⚡ Hecho con ❤️ y Python**

_Si este proyecto te resultó útil, ¡dale una ⭐!_
