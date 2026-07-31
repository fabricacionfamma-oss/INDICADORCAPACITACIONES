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
    
    # Tomamos las primeras 4 columnas dinámicamente (Legajo/Leg, Apellido, Nombre, Area)
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
    
    # Limpieza específica para Asistencia (P, A)
    df_asis_melt['Estado'] = df_asis_melt['Estado'].astype(str).str.upper().str.strip()
    df_asis_melt['Estado'] = df_asis_melt['Estado'].replace({
        'P': 'Presente',
        'A': 'Ausente / Falta',
        'NAN': 'Sin Registro'
    })
    
    # Limpieza básica para Calidad
    df_cal_melt['Estado'] = df_cal_melt['Estado'].astype(str).str.title().str.strip()
    df_cal_melt['Estado'] = df_cal_melt['Estado'].replace({'Nan': 'Sin evaluar'})

    st.success("¡Datos procesados correctamente!")

    # 3. Creación de las Pestañas Visuales 
    tab1, tab2 = st.tabs([
        "📈 Resumen General", 
        "👤 Perfil del Participante (360°)"
    ])
    
    # --- PESTAÑA 1: VISTA GENERAL ---
    with tab1:
        st.header("Resumen Global de Formaciones")
        
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
                color_discrete_map={'Presente': '#00CC96', 'Ausente / Falta': '#EF553B'}
            )
            col_cen.plotly_chart(fig_asis_global, use_container_width=True)
        else:
            st.info("No hay registros suficientes para calcular la asistencia global.")
        
        st.divider()
        
        # 2. GRÁFICOS DETALLADOS POR CAPACITACIÓN + LISTA DE AUSENTES
        st.subheader("Asistencia detallada por Capacitación")
        
        todas_las_capacitaciones = df_asis_melt['Capacitación'].unique()
        capacitaciones_con_datos = df_asis_validos['Capacitación'].unique()
        capacitaciones_pendientes = [cap for cap in todas_las_capacitaciones if cap not in capacitaciones_con_datos]
        
        cols_torta = st.columns(3)
        
        for i, cap in enumerate(capacitaciones_con_datos):
            df_cap = df_asis_validos[df_asis_validos['Capacitación'] == cap]
            
            fig_torta = px.pie(
                df_cap, 
                names='Estado', 
                title=f"{cap}",
                hole=0.3,
                color='Estado',
                color_discrete_map={'Presente': '#00CC96', 'Ausente / Falta': '#EF553B'}
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
                    st.success("✨ Asistencia perfecta")
            
        if capacitaciones_pendientes:
            st.divider()
            st.markdown("### ⏳ Capacitaciones Pendientes (Sin registros)")
            for cap_pend in capacitaciones_pendientes:
                st.warning(f"🔹 **{cap_pend}**")
                

    # --- PESTAÑA 2: VISTA UNIFICADA POR PARTICIPANTE ---
    with tab2:
        participantes = sorted([str(p) for p in df_asis['Nombre Completo'].unique() if str(p).lower() not in ['nan nan', 'nan']])
        seleccion_participante = st.selectbox("Buscar Empleado:", participantes)
        
        datos_usuario = df_asis[df_asis['Nombre Completo'] == seleccion_participante].iloc[0]
        
        st.markdown(f"### Perfil de: **{seleccion_participante}**")
        st.markdown(f"**Legajo:** {datos_usuario[cols_identificadoras_asis[0]]} | **Área:** {datos_usuario[cols_identificadoras_asis[3]]}")
        st.divider()
        
        # --- SECCIÓN 1: ASISTENCIA Y CALIDAD (Rojas) ---
        datos_asis_part = df_asis_melt[df_asis_melt['Nombre Completo'] == seleccion_participante]
        datos_cal_part = df_cal_melt[df_cal_melt['Nombre Completo'] == seleccion_participante]
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Control de Asistencia")
            datos_asis_validos_part = datos_asis_part[datos_asis_part['Estado'] != 'Sin Registro']
            if not datos_asis_validos_part.empty:
                fig_asis_part = px.pie(
                    datos_asis_validos_part, names='Estado', title="Asistencias vs Ausencias",
                    color='Estado', color_discrete_map={'Presente': '#00CC96', 'Ausente / Falta': '#EF553B'}
                )
                st.plotly_chart(fig_asis_part, use_container_width=True)
            else:
                st.info("No hay registros de asistencia para graficar.")
            
            faltas = datos_asis_part[datos_asis_part['Estado'] == 'Ausente / Falta']['Capacitación'].tolist()
            st.markdown("**Capacitaciones Ausentes:**")
            if faltas:
                for cap in faltas:
                    st.error(f"❌ {cap}")
            else:
                st.success("✨ No registra ausencias.")
                
        with col4:
            st.subheader("Calidad de Aplicación")
            tabla_calidad = datos_cal_part[['Capacitación', 'Estado']].reset_index(drop=True)
            st.dataframe(tabla_calidad, use_container_width=True)

        st.divider()

        # --- SECCIÓN 2: SEGUIMIENTO SEMANAL (Verdes) - TABLA AUTOMÁTICA ---
        st.subheader("📅 Seguimiento Semanal de Aplicación")
        
        if hojas_verdes:
            # Buscar coincidencia exacta o contenida (ej: si la pestaña se llama "BAZAN" y el usuario es "PABLO BAZAN")
            hoja_encontrada = None
            for hoja in hojas_verdes:
                if hoja.lower().strip() in seleccion_participante.lower():
                    hoja_encontrada = hoja
                    break
            
            if hoja_encontrada:
                df_verde = xls[hoja_encontrada].copy()
                df_verde = df_verde.dropna(how='all') # Limpiar filas 100% vacías
                
                if not df_verde.empty:
                    # Definir lógica de colores para la tabla
                    def colorear_celdas(val):
                        if pd.isna(val) or str(val).strip() == "":
                            return ""
                        
                        val_str = str(val).strip().title()
                        
                        if val_str == "Ok":
                            return "background-color: #00CC96; color: black; font-weight: bold;" # Verde
                        elif val_str == "Nok":
                            return "background-color: #EF553B; color: white; font-weight: bold;" # Rojo
                        else:
                            return "background-color: #9C27B0; color: white; font-weight: bold;" # Violeta
                    
                    # Coloreamos todas las columnas excepto la primera (asumiendo que es "SEMANA")
                    cols_indicadores = df_verde.columns[1:]
                    
                    try:
                        df_estilo = df_verde.style.map(colorear_celdas, subset=cols_indicadores)
                    except AttributeError:
                        df_estilo = df_verde.style.applymap(colorear_celdas, subset=cols_indicadores)
                    
                    st.dataframe(df_estilo, use_container_width=True)
                else:
                    st.info("La pestaña de este participante está vacía.")
            else:
                st.warning(f"No se encontró una pestaña de seguimiento semanal (verde) registrada para **{seleccion_participante}**.")
        else:
            st.warning("No se detectaron hojas adicionales (verdes) en el archivo.")
