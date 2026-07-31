import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Tablero de Indicadores SPT", layout="wide")

st.title("📊 Tablero de Indicadores SPT")
st.write("Análisis de Asistencia a la Formación y Calidad de Aplicación.")

# 1. Carga del archivo
archivo_subido = st.file_uploader("Sube el archivo Tablero_Indicadores SPT.xlsx", type=['xlsx'])

if archivo_subido is not None:
    # Leer todas las pestañas del Excel
    xls = pd.read_excel(archivo_subido, sheet_name=None)
    nombres_hojas = list(xls.keys())
    
    st.sidebar.header("Configuración de Pestañas")
    st.sidebar.write("Selecciona cuáles son las pestañas rojas:")
    
    # Intentar autodetectar las hojas por nombre (por si contienen la palabra)
    hoja_asis_def = next((h for h in nombres_hojas if 'asistencia' in h.lower()), nombres_hojas[0])
    hoja_cal_def = next((h for h in nombres_hojas if 'calidad' in h.lower()), nombres_hojas[-1])
    
    # El usuario confirma qué hoja es cuál en el menú lateral
    hoja_asistencia = st.sidebar.selectbox("Pestaña de Asistencia:", nombres_hojas, index=nombres_hojas.index(hoja_asis_def))
    hoja_calidad = st.sidebar.selectbox("Pestaña de Calidad:", nombres_hojas, index=nombres_hojas.index(hoja_cal_def))
    
    # 2. Procesamiento de Datos
    df_asis = xls[hoja_asistencia].copy()
    df_cal = xls[hoja_calidad].copy()
    
    # Identificamos las primeras 4 columnas (Legajo, Apellido, Nombre, Area)
    cols_identificadoras = list(df_asis.columns[:4])
    
    # Creamos una columna combinada de Nombre y Apellido para el buscador de la app
    # Asumimos el orden de tu imagen: [0] Legajo, [1] Apellido, [2] Nombre, [3] Area
    col_apellido = df_asis.columns[1]
    col_nombre = df_asis.columns[2]
    
    df_asis['Nombre Completo'] = df_asis[col_nombre].astype(str) + " " + df_asis[col_apellido].astype(str)
    df_cal['Nombre Completo'] = df_cal[col_nombre].astype(str) + " " + df_cal[col_apellido].astype(str)
    
    # Sumamos la nueva columna a las identificadoras para que no se mezcle con las capacitaciones
    cols_id_finales = cols_identificadoras + ['Nombre Completo']
    
    # Desdoblar (Melt) las columnas de capacitaciones en filas
    df_asis_melt = df_asis.melt(id_vars=cols_id_finales, var_name="Capacitación", value_name="Estado Asistencia")
    df_cal_melt = df_cal.melt(id_vars=cols_id_finales, var_name="Capacitación", value_name="Estado Calidad")
    
    # Limpieza básica: Si la celda está vacía, asumimos que "No Asistió" o "Sin evaluar"
    df_asis_melt['Estado Asistencia'] = df_asis_melt['Estado Asistencia'].fillna("Falta / No Asistió")
    df_asis_melt['Estado Asistencia'] = df_asis_melt['Estado Asistencia'].astype(str).str.title()
    
    df_cal_melt['Estado Calidad'] = df_cal_melt['Estado Calidad'].fillna("Sin evaluar")
    df_cal_melt['Estado Calidad'] = df_cal_melt['Estado Calidad'].astype(str).str.title()

    st.success("¡Datos procesados correctamente!")

    # 3. Creación de las Pestañas Visuales en Streamlit
    tab1, tab2 = st.tabs(["📈 Vista General (Totales)", "👤 Vista por Participante"])
    
    # --- PESTAÑA 1: VISTA GENERAL ---
    with tab1:
        st.header("Resumen General de todas las Capacitaciones")
        col1, col2 = st.columns(2)
        
        fig_asis_gen = px.pie(
            df_asis_melt, 
            names='Estado Asistencia', 
            title="Porcentaje Total de Asistencia",
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        col1.plotly_chart(fig_asis_gen, use_container_width=True)
        
        fig_cal_gen = px.pie(
            df_cal_melt, 
            names='Estado Calidad', 
            title="Distribución Total de Calidad",
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        col2.plotly_chart(fig_cal_gen, use_container_width=True)


    # --- PESTAÑA 2: VISTA POR PARTICIPANTE ---
    with tab2:
        # Obtenemos la lista de participantes limpios (sin nulos ni valores extraños)
        participantes = sorted([p for p in df_asis['Nombre Completo'].unique() if str(p).lower() != 'nan nan'])
        
        seleccion_participante = st.selectbox("Buscar/Seleccionar Participante:", participantes)
        
        # Obtenemos los datos del participante seleccionado (Legajo, Área, etc.)
        datos_usuario = df_asis[df_asis['Nombre Completo'] == seleccion_participante].iloc[0]
        
        st.markdown(f"### Desempeño de: **{seleccion_participante}**")
        st.markdown(f"**Legajo:** {datos_usuario[cols_identificadoras[0]]} | **Área:** {datos_usuario[cols_identificadoras[3]]}")
        st.divider()
        
        # Filtramos los datos derretidos solo para el participante
        datos_asis_part = df_asis_melt[df_asis_melt['Nombre Completo'] == seleccion_participante]
        datos_cal_part = df_cal_melt[df_cal_melt['Nombre Completo'] == seleccion_participante]
        
        col3, col4 = st.columns(2)
        
        # --- Asistencia del Participante ---
        with col3:
            st.subheader("Control de Asistencia")
            fig_asis_part = px.pie(
                datos_asis_part, 
                names='Estado Asistencia', 
                title="Proporción Asistida vs Faltas"
            )
            st.plotly_chart(fig_asis_part, use_container_width=True)
            
            # Detectar faltas
            condicion_falta = datos_asis_part['Estado Asistencia'].str.contains('Falta|No|Ausente|Nan', case=False, na=False)
            capacitaciones_faltantes = datos_asis_part[condicion_falta]['Capacitación'].tolist()
            
            st.markdown("**Capacitaciones Pendientes / Ausentes:**")
            if capacitaciones_faltantes:
                for cap in capacitaciones_faltantes:
                    st.error(f"❌ {cap}")
            else:
                st.success("✨ ¡Asistencia completa! No debe ninguna capacitación.")
                
        # --- Calidad del Participante ---
        with col4:
            st.subheader("Calidad de Aplicación")
            fig_cal_part = px.pie(
                datos_cal_part, 
                names='Estado Calidad', 
                title="Distribución de Calidad"
            )
            st.plotly_chart(fig_cal_part, use_container_width=True)
            
            st.markdown("**Detalle por Capacitación:**")
            tabla_calidad = datos_cal_part[['Capacitación', 'Estado Calidad']].reset_index(drop=True)
            st.dataframe(tabla_calidad, use_container_width=True)
