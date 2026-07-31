import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Tablero de Indicadores SPT", layout="wide")

st.title("📊 Tablero de Indicadores SPT")
st.write("Análisis de Asistencia, Calidad de Aplicación y Seguimiento Semanal.")

# 1. Carga del archivo
archivo_subido = st.file_uploader("Sube el archivo Tablero_Indicadores SPT.xlsx", type=['xlsx'])

if archivo_subido is not None:
    # Leer todas las pestañas del Excel
    xls = pd.read_excel(archivo_subido, sheet_name=None)
    nombres_hojas = list(xls.keys())
    
    st.sidebar.header("Configuración de Pestañas")
    
    # Intentar autodetectar las hojas por nombre
    hoja_asis_def = next((h for h in nombres_hojas if 'asistencia' in h.lower()), nombres_hojas[0])
    hoja_cal_def = next((h for h in nombres_hojas if 'calidad' in h.lower()), nombres_hojas[-1])
    
    # El usuario confirma qué hoja es cuál en el menú lateral
    hoja_asistencia = st.sidebar.selectbox("Pestaña de Asistencia (Roja):", nombres_hojas, index=nombres_hojas.index(hoja_asis_def))
    hoja_calidad = st.sidebar.selectbox("Pestaña de Calidad (Roja):", nombres_hojas, index=nombres_hojas.index(hoja_cal_def))
    
    # Todas las demás hojas se asumen como VERDES (Participantes)
    hojas_verdes = [h for h in nombres_hojas if h not in [hoja_asistencia, hoja_calidad]]
    
    # 2. Procesamiento de Datos Hojas Rojas (Asistencia y Calidad)
    df_asis = xls[hoja_asistencia].copy()
    df_cal = xls[hoja_calidad].copy()
    
    # Tomamos las primeras 4 columnas dinámicamente
    cols_identificadoras_asis = list(df_asis.columns[:4])
    cols_identificadoras_cal = list(df_cal.columns[:4])
    
    # Crear columna de Nombre Completo
    df_asis['Nombre Completo'] = df_asis[df_asis.columns[2]].astype(str) + " " + df_asis[df_asis.columns[1]].astype(str)
    df_cal['Nombre Completo'] = df_cal[df_cal.columns[2]].astype(str) + " " + df_cal[df_cal.columns[1]].astype(str)
    
    cols_id_finales_asis = cols_identificadoras_asis + ['Nombre Completo']
    cols_id_finales_cal = cols_identificadoras_cal + ['Nombre Completo']
    
    # Desdoblar (Melt)
    df_asis_melt = df_asis.melt(id_vars=cols_id_finales_asis, var_name="Capacitación", value_name="Estado")
    df_cal_melt = df_cal.melt(id_vars=cols_id_finales_cal, var_name="Capacitación", value_name="Estado")
    
    # --- LIMPIEZA ESTRICTA PARA ASISTENCIA (Regla: A, P, N/A, PENDIENTE) ---
    def normalizar_asistencia(x):
        val = str(x).upper().strip()
        if val in ['P', 'PRESENTE']:
            return 'Presente'
        elif val in ['A', 'AUSENTE', 'FALTA']:
            return 'Ausente / Falta'
        elif val in ['N/A', 'NA', 'NO APLICA']:
            return 'No Aplica'
        elif val in ['PENDIENTE']:
            return 'Pendiente'
        else:
            return 'Sin Registro' # Por si acaso se cuela una celda vacía por error
            
    df_asis_melt['Estado'] = df_asis_melt['Estado'].apply(normalizar_asistencia)
    
    # --- LIMPIEZA BÁSICA PARA CALIDAD ---
    def normalizar_calidad(x):
        val = str(x).title().strip()
        if val in ['Nan', 'None', 'Null', '']:
            return 'Sin Evaluar'
        return val
        
    df_cal_melt['Estado'] = df_cal_melt['Estado'].apply(normalizar_calidad)

    # MAPA DE COLORES ESTÁNDAR PARA GRÁFICOS
    mapa_colores = {
        'Presente': '#00CC96',       # Verde
        'Ausente / Falta': '#EF553B',# Rojo
        'No Aplica': '#B0BEC5',      # Gris
        'Pendiente': '#FFC107'       # Amarillo/Dorado
    }

    st.success("¡Datos procesados correctamente!")

    # 3. Creación de las Pestañas Visuales 
    tab1, tab2 = st.tabs([
        "📈 Resumen General", 
        "👤 Perfil del Participante (360°)"
    ])
    
    # --- PESTAÑA 1: VISTA GENERAL ---
    with tab1:
        st.header("Resumen Global de Formaciones")
        
        # Filtramos 'Sin Registro' pero mantenemos los Pendientes
        df_asis_validos = df_asis_melt[df_asis_melt['Estado'] != 'Sin Registro']
        
        # 1. GRÁFICO GLOBAL DE ASISTENCIA
        st.subheader("Asistencia Global (Total de todas las capacitaciones)")
        if not df_asis_validos.empty:
            col_izq, col_cen, col_der = st.columns([1, 2, 1])
            fig_asis_global = px.pie(
                df_asis_validos, 
                names='Estado', 
                hole=0.3,
                color='Estado',
                color_discrete_map=mapa_colores
            )
            col_cen.plotly_chart(fig_asis_global, use_container_width=True)
        else:
            st.info("No hay registros suficientes para calcular la asistencia global.")
        
        st.divider()
        
        # 2. GRÁFICOS DETALLADOS POR CAPACITACIÓN + LISTA DE AUSENTES
        st.subheader("Asistencia detallada por Capacitación")
        
        capacitaciones_con_datos = df_asis_validos['Capacitación'].unique()
        cols_torta = st.columns(3)
        
        for i, cap in enumerate(capacitaciones_con_datos):
            df_cap = df_asis_validos[df_asis_validos['Capacitación'] == cap]
            
            fig_torta = px.pie(
                df_cap, 
                names='Estado', 
                title=f"{cap}",
                hole=0.3,
                color='Estado',
                color_discrete_map=mapa_colores
            )
            
            fig_torta.update_layout(
                showlegend=True, 
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                title_x=0.5, 
                title_font_size=14,
                margin=dict(b=0) 
            )
            
            with cols_torta[i % 3]:
                st.plotly_chart(fig_torta, use_container_width=True)
                
                ausentes = df_cap[df_cap['Estado'] == 'Ausente / Falta']['Nombre Completo'].tolist()
                
                if ausentes:
                    with st.expander(f"Ausentes ({len(ausentes)})"):
                        for persona in ausentes:
                            st.write(f"❌ {persona}")
                else:
                    st.success("✨ Sin ausencias registradas")

    # --- PESTAÑA 2: VISTA UNIFICADA POR PARTICIPANTE ---
    with tab2:
        participantes = sorted([str(p) for p in df_asis['Nombre Completo'].unique() if str(p).lower() not in ['nan nan', 'nan']])
        seleccion_participante = st.selectbox("Buscar Empleado:", participantes)
        
        datos_usuario = df_asis[df_asis['Nombre Completo'] == seleccion_participante].iloc[0]
        
        st.markdown(f"### Perfil de: **{seleccion_participante}**")
        st.markdown(f"**Legajo:** {datos_usuario[cols_identificadoras_asis[0]]} | **Área:** {datos_usuario[cols_identificadoras_asis[3]]}")
        st.divider()
        
        # Filtrar datos del participante
        datos_asis_part = df_asis_melt[df_asis_melt['Nombre Completo'] == seleccion_participante]
        datos_cal_part = df_cal_melt[df_cal_melt['Nombre Completo'] == seleccion_participante]
        
        # --- SECCIÓN 1: ASISTENCIA (Arriba) ---
        st.subheader("Control de Asistencia")
        col_torta, col_listas = st.columns([1.5, 1])
        
        with col_torta:
            datos_asis_validos_part = datos_asis_part[datos_asis_part['Estado'] != 'Sin Registro']
            
            if not datos_asis_validos_part.empty:
                fig_asis_part = px.pie(
                    datos_asis_validos_part, names='Estado', title="Proporción General",
                    color='Estado', color_discrete_map=mapa_colores
                )
                st.plotly_chart(fig_asis_part, use_container_width=True)
            else:
                st.info("No hay registros válidos de asistencia para graficar.")
                
        with col_listas:
            # Lista de Ausencias
            faltas = datos_asis_part[datos_asis_part['Estado'] == 'Ausente / Falta']['Capacitación'].tolist()
            st.markdown("**❌ Capacitaciones Ausentes:**")
            if faltas:
                for cap in faltas:
                    st.write(f"- {cap}")
            else:
                st.success("No registra ausencias.")
                
            st.write("---")
            
            # Lista de Pendientes (Actualizado)
            pendientes = datos_asis_part[datos_asis_part['Estado'] == 'Pendiente']['Capacitación'].tolist()
            st.markdown("**⏳ Capacitaciones Pendientes:**")
            if pendientes:
                for cap in pendientes:
                    st.write(f"- {cap}")
            else:
                st.info("Sin capacitaciones pendientes.")
                
        st.divider()

        # --- SECCIÓN 2: CALIDAD Y RADAR DE SKILLS ---
        st.subheader("Calidad y Mapa de Capacitaciones")
        col_cal, col_radar = st.columns(2)
        
        with col_cal:
            st.markdown("**Evaluación de Calidad**")
            datos_cal_validos = datos_cal_part[datos_cal_part['Estado'] != 'Sin Evaluar']
            
            if not datos_cal_validos.empty:
                tabla_calidad = datos_cal_validos[['Capacitación', 'Estado']].reset_index(drop=True)
                st.dataframe(tabla_calidad, use_container_width=True)
            else:
                st.info("No hay evaluaciones de calidad registradas.")
                
        with col_radar:
            st.markdown("**Radar de Capacitaciones Completadas**")
            # En el radar, Presente = 1. Todo lo demás (Ausente, N/A, Pendiente) no suma punto = 0
            df_radar = datos_asis_part.copy()
            df_radar['Valor'] = df_radar['Estado'].apply(lambda x: 1 if x == 'Presente' else 0)
            
            if not df_radar.empty:
                fig_radar = px.line_polar(
                    df_radar, 
                    r='Valor', 
                    theta='Capacitación', 
                    line_close=True,
                    range_r=[0, 1]
                )
                
                fig_radar.update_traces(fill='toself', line_color='#00CC96', marker=dict(size=8))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=False)
                    ),
                    margin=dict(t=30, b=30, l=30, r=30)
                )
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("No hay capacitaciones para generar el mapa.")

        st.divider()

        # --- SECCIÓN 3: SEGUIMIENTO SEMANAL (Verdes) ---
        st.subheader("📅 Seguimiento Semanal de Aplicación")
        
        if hojas_verdes:
            hoja_encontrada = None
            apellido_prob = seleccion_participante.split()[-1].lower()
            
            for hoja in hojas_verdes:
                if hoja.lower().strip() in seleccion_participante.lower():
                    hoja_encontrada = hoja
                    break
            
            if hoja_encontrada:
                df_verde = xls[hoja_encontrada].copy()
                df_verde = df_verde.dropna(how='all')
                
                if not df_verde.empty:
                    def colorear_celdas(val):
                        if pd.isna(val) or str(val).strip() == "":
                            return ""
                        
                        val_str = str(val).strip().title()
                        
                        if val_str == "Ok":
                            return "background-color: #00CC96; color: black; font-weight: bold;" 
                        elif val_str == "Nok":
                            return "background-color: #EF553B; color: white; font-weight: bold;" 
                        else:
                            return "background-color: #9C27B0; color: white; font-weight: bold;" 
                    
                    cols_indicadores = df_verde.columns[1:]
                    
                    try:
                        df_estilo = df_verde.style.map(colorear_celdas, subset=cols_indicadores)
                    except AttributeError:
                        df_estilo = df_verde.style.applymap(colorear_celdas, subset=cols_indicadores)
                    
                    st.dataframe(df_estilo, use_container_width=True)
                else:
                    st.info("La pestaña de este participante está vacía.")
            else:
                st.warning(f"No se encontró una pestaña de seguimiento semanal registrada para **{seleccion_participante}**.")
        else:
            st.warning("No se detectaron hojas adicionales (verdes) en el archivo.")
