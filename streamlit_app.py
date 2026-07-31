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
    tab1, tab2, tab3 = st.tabs([
        "📈 Resumen General", 
        "👤 Detalle Asistencia y Calidad", 
        "📅 Evolución Semanal (Hojas Verdes)"
    ])
    
    # --- PESTAÑA 1: VISTA GENERAL ---
    with tab1:
        st.header("Resumen Global de Formaciones")
        
        # --- Modificación: Gráficos de torta por cada capacitación ---
        st.subheader("Asistencia detallada por Capacitación")
        df_asis_validos = df_asis_melt[df_asis_melt['Estado'] != 'Sin Registro']
        lista_capacitaciones = df_asis_validos['Capacitación'].unique()
        
        # Creamos 3 columnas para organizar las tortas en forma de grilla
        cols_torta = st.columns(3)
        
        for i, cap in enumerate(lista_capacitaciones):
            df_cap = df_asis_validos[df_asis_validos['Capacitación'] == cap]
            
            # Graficar solo si hay datos para esa capacitación
            if not df_cap.empty:
                fig_torta = px.pie(
                    df_cap, 
                    names='Estado', 
                    title=f"Asistencia: {cap}",
                    hole=0.3,
                    color='Estado',
                    color_discrete_map={'Presente': '#00CC96', 'Ausente / Falta': '#EF553B'}
                )
                
                # Ajustar el diseño para que se vea limpio en tamaño pequeño
                fig_torta.update_layout(
                    showlegend=True, 
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    title_x=0.5, 
                    title_font_size=14
                )
                
                # Asignar cada gráfico a una columna en secuencia
                cols_torta[i % 3].plotly_chart(fig_torta, use_container_width=True)
        
        st.divider()
        
        # Gráfico General de Calidad
        st.subheader("Distribución Total de Calidad de Aplicación")
        col_vacia1, col_centro, col_vacia2 = st.columns([1, 2, 1]) # Centrar el gráfico
        fig_cal_gen = px.pie(
            df_cal_melt[df_cal_melt['Estado'] != 'Sin Evaluar'], 
            names='Estado', 
            hole=0.3
        )
        col_centro.plotly_chart(fig_cal_gen, use_container_width=True)

    # --- PESTAÑA 2: VISTA POR PARTICIPANTE (ROJAS) ---
    with tab2:
        participantes = sorted([str(p) for p in df_asis['Nombre Completo'].unique() if str(p).lower() not in ['nan nan', 'nan']])
        seleccion_participante = st.selectbox("Buscar Empleado (Asistencia/Calidad):", participantes)
        
        # Filtramos datos del participante seleccionado
        datos_usuario = df_asis[df_asis['Nombre Completo'] == seleccion_participante].iloc[0]
        
        st.markdown(f"### Desempeño de: **{seleccion_participante}**")
        st.markdown(f"**Legajo:** {datos_usuario[cols_identificadoras_asis[0]]} | **Área:** {datos_usuario[cols_identificadoras_asis[3]]}")
        st.divider()
        
        datos_asis_part = df_asis_melt[df_asis_melt['Nombre Completo'] == seleccion_participante]
        datos_cal_part = df_cal_melt[df_cal_melt['Nombre Completo'] == seleccion_participante]
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Control de Asistencia")
            # Graficar solo si hay datos reales
            datos_asis_validos_part = datos_asis_part[datos_asis_part['Estado'] != 'Sin Registro']
            if not datos_asis_validos_part.empty:
                fig_asis_part = px.pie(
                    datos_asis_validos_part, names='Estado', title="Asistencias vs Ausencias",
                    color='Estado', color_discrete_map={'Presente': '#00CC96', 'Ausente / Falta': '#EF553B'}
                )
                st.plotly_chart(fig_asis_part, use_container_width=True)
            else:
                st.info("No hay registros de asistencia para graficar.")
            
            # Detectar faltas
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

    # --- PESTAÑA 3: SEGUIMIENTO SEMANAL (VERDES) ---
    with tab3:
        st.header("Seguimiento Semanal de Aplicación (Hojas Verdes)")
        if hojas_verdes:
            hoja_verde_sel = st.selectbox("Selecciona la pestaña del participante:", hojas_verdes)
            
            # Leer la hoja verde seleccionada
            df_verde = xls[hoja_verde_sel].copy()
            
            # Asumimos que la primera columna es "SEMANA"
            col_semana = df_verde.columns[0]
            
            st.write(f"**Datos registrados para:** {hoja_verde_sel}")
            st.dataframe(df_verde.dropna(how='all'), use_container_width=True)
            
            # Transformar para graficar Ok vs Nok
            df_verde_melt = df_verde.melt(id_vars=[col_semana], var_name="Indicador", value_name="Resultado")
            df_verde_melt['Resultado'] = df_verde_melt['Resultado'].astype(str).str.capitalize().str.strip()
            
            # Filtrar solo los Ok y Nok para el gráfico
            df_grafico_verde = df_verde_melt[df_verde_melt['Resultado'].isin(['Ok', 'Nok'])]
            
            if not df_grafico_verde.empty:
                st.subheader("Evolución de Ok / Nok por Semana")
                fig_verde = px.histogram(
                    df_grafico_verde, 
                    x=col_semana, 
                    color="Resultado", 
                    barmode="group",
                    color_discrete_map={'Ok': '#00CC96', 'Nok': '#EF553B'},
                    title="Cantidad de Ok vs Nok a lo largo de las semanas"
                )
                fig_verde.update_layout(yaxis_title="Cantidad de Indicadores", xaxis_title="Semana")
                st.plotly_chart(fig_verde, use_container_width=True)
            else:
                st.info("No hay suficientes valores 'Ok' o 'Nok' registrados para generar el gráfico semanal.")
        else:
            st.warning("No se detectaron hojas adicionales (verdes) en el archivo.")
