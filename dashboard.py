import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURACIÓN Y ESTÉTICA AVANZADA (CSS)
# ==========================================
st.set_page_config(page_title="ERP Lavandería Díaz", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 8px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        border-left: 5px solid #0056b3; 
        transition: transform 0.2s ease-in-out, box-shadow 0.2s;
    }
    .stMetric:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f8f9fa; 
        border-radius: 4px 4px 0px 0px; 
        padding: 12px 24px; 
        font-weight: 600; 
        border: 1px solid #e9ecef; 
        border-bottom: none; 
        color: #495057;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #0056b3; 
        color: white !important; 
    }
    h1, h2, h3 { color: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y TRANSFORMACIÓN DE DATOS (ETL)
# ==========================================
@st.cache_data
def cargar_datos_maestros():
    df = pd.read_excel('Base_Maestra_Lavanderia.xlsx')
    df['OEE_Planta'] = (df['Horas_Operativas'] / df['Horas_Planificadas']) * (df['Prendas_OK'] / df['Total_Prendas']) * 100
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
    # NUEVO: Creamos una columna que agrupa por Año y Mes (Ej: "2025 - 09")
    df['Periodo_Mensual'] = df['Fecha'].dt.strftime('%Y - %m')
    
    df = df.sort_values('Fecha')
    return df

df = cargar_datos_maestros()

# ==========================================
# 3. BARRA LATERAL (HERRAMIENTAS Y FILTROS)
# ==========================================
st.sidebar.title("Panel de Herramientas")
st.sidebar.markdown("---")

# NUEVO: Filtro de meses extraído directamente de la base de datos (2025-2026)
periodos_disponibles = sorted(df['Periodo_Mensual'].unique().tolist())
periodos_sel = st.sidebar.multiselect("Seleccionar Meses:", periodos_disponibles, default=periodos_disponibles)

telas_sel = st.sidebar.multiselect("Tipo de Tela:", df['Tela'].unique().tolist(), default=df['Tela'].unique().tolist())
prendas_sel = st.sidebar.multiselect("Tipo de Prenda:", df['Prenda'].unique().tolist(), default=df['Prenda'].unique().tolist())

st.sidebar.markdown("---")
meta_oee = st.sidebar.slider("Meta OEE de Planta (%)", 50, 100, 85)

# Lógica de filtrado dinámico cruzado
if not periodos_sel or not telas_sel or not prendas_sel:
    # Si el usuario desmarca todas las opciones, devolvemos un DataFrame vacío
    df_filtrado = pd.DataFrame(columns=df.columns)
else:
    df_filtrado = df[
        (df['Periodo_Mensual'].isin(periodos_sel)) & 
        (df['Tela'].isin(telas_sel)) & 
        (df['Prenda'].isin(prendas_sel))
    ]

# ==========================================
# 4. PANEL PRINCIPAL: KPIs 
# ==========================================
st.title("Sistema ERP de Producción y Rentabilidad")

if df_filtrado.empty:
    st.error("No hay datos para la combinación de filtros seleccionada. Asegúrese de elegir al menos un mes, una tela y una prenda.")
else:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Volumen Procesado", f"{df_filtrado['Total_Prendas'].sum():,.0f} uds")
    col2.metric("Ganancia Proyectada", f"S/ {df_filtrado['Ganancia_S/'].sum():,.2f}")
    oee_actual = df_filtrado['OEE_Planta'].mean()
    col3.metric("OEE de Planta", f"{oee_actual:.1f}%")
    otif_pct = (len(df_filtrado[df_filtrado['OTIF'] == 'A Tiempo']) / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0
    col4.metric("Nivel de Servicio (OTIF)", f"{otif_pct:.1f}%")

    if oee_actual >= meta_oee:
        st.success(f"Operación Óptima: El OEE supera la meta en {oee_actual - meta_oee:.1f}%.")
    else:
        st.warning(f"Alerta de Rendimiento: OEE {meta_oee - oee_actual:.1f}% por debajo de la meta. Revise tiempos muertos.")

    st.markdown("---")

    # ==========================================
    # 5. MÓDULOS DE ANÁLISIS (6 PESTAÑAS)
    # ==========================================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Producción y Eficiencia", 
        "Logística y Flujo", 
        "Calidad y Tiempos", 
        "Finanzas", 
        "Simulador ERP",
        "Monitor de Planta (En Vivo)"
    ])

    # --- PESTAÑA 1: PRODUCCIÓN ---
    with tab1:
        col_1a, col_1b = st.columns(2)
        with col_1a:
            st.subheader("Medidor de Eficiencia")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta", value=oee_actual, delta={'reference': meta_oee, 'position': "bottom"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#0056b3"},
                       'steps': [{'range': [0, 65], 'color': "#f8d7da"}, {'range': [65, meta_oee], 'color': "#fff3cd"}, {'range': [meta_oee, 100], 'color': "#d4edda"}],
                       'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': meta_oee}}))
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.caption(f"Conclusión: La eficiencia general es {oee_actual:.1f}%. Este KPI evalúa la utilización real de la capacidad instalada.")
            
        with col_1b:
            st.subheader("Jerarquía de Producción")
            fig_tree = px.treemap(df_filtrado, path=['Tela', 'Prenda', 'Proceso'], values='Total_Prendas', color='Total_Prendas', color_continuous_scale='Blues')
            st.plotly_chart(fig_tree, use_container_width=True)
            st.caption("Conclusión: Identifica las combinaciones de tela y proceso que acaparan el mayor volumen de la planta.")
            
        col_1c, col_1d = st.columns(2)
        with col_1c:
            st.subheader("Rendimiento OEE por Máquina")
            df_maq = df_filtrado.groupby('Maquina')['OEE_Planta'].mean().reset_index().sort_values('OEE_Planta', ascending=False)
            fig_maq = px.bar(df_maq, x='Maquina', y='OEE_Planta', text_auto='.1f', color='OEE_Planta', color_continuous_scale='Blues')
            fig_maq.add_hline(y=meta_oee, line_dash="dash", line_color="red")
            st.plotly_chart(fig_maq, use_container_width=True)
            st.caption("Conclusión: Permite focalizar inspecciones mecánicas en los equipos con las barras más bajas de rendimiento.")
            
        with col_1d:
            st.subheader("Volumen por Prenda")
            df_prenda = df_filtrado.groupby('Prenda')['Total_Prendas'].sum().reset_index().sort_values('Total_Prendas', ascending=False)
            fig_donut = px.pie(df_prenda, names='Prenda', values='Total_Prendas', hole=0.4)
            st.plotly_chart(fig_donut, use_container_width=True)
            prenda_top = df_prenda.iloc[0]['Prenda'] if not df_prenda.empty else "N/A"
            st.caption(f"Conclusión: {prenda_top} es la categoría de mayor tránsito. Fundamental para prever capacidad de almacén.")

    # --- PESTAÑA 2: LOGÍSTICA ---
    with tab2:
        col_2a, col_2b = st.columns(2)
        with col_2a:
            st.subheader("Cuellos de Botella End-to-End")
            promedios_e2e = pd.DataFrame({
                'Etapa': ['1. Almacén Gral', '2. Almacén Trans.', '3. Maquinaria', '4. Plancha Total'],
                'Horas': [df_filtrado['Almacen_Gral_Hrs'].mean(), df_filtrado['Almacen_Trans_Hrs'].mean(), df_filtrado['Horas_Operativas'].mean(), (df_filtrado['Vaporizado_Hrs'] + df_filtrado['Pretinado_Hrs'] + df_filtrado['Planchado_Hrs']).mean()]
            })
            fig_funnel = px.funnel(promedios_e2e, x='Horas', y='Etapa')
            st.plotly_chart(fig_funnel, use_container_width=True)
            st.caption("Conclusión: El embudo detecta en qué etapa exacta las órdenes acumulan la mayor cantidad de horas estancadas.")
            
        with col_2b:
            st.subheader("Flujo Operativo (Sankey)")
            fuentes = [0, 0, 1, 1] 
            destinos = [2, 3, 2, 3] 
            valores = [df_filtrado[df_filtrado['Tela']=='DENIM']['Total_Prendas'].sum(), df_filtrado[df_filtrado['Tela']=='DRILL']['Total_Prendas'].sum(),
                       df_filtrado[df_filtrado['Proceso']=='Suavizado']['Total_Prendas'].sum(), df_filtrado[df_filtrado['Proceso']!='Suavizado']['Total_Prendas'].sum()]
            fig_sankey = go.Figure(data=[go.Sankey(node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=["Denim", "Drill", "Lavado Básico", "Proceso Complejo"]), link=dict(source=fuentes, target=destinos, value=valores))])
            st.plotly_chart(fig_sankey, use_container_width=True)
            st.caption("Conclusión: Mapa logístico que ilustra la proporción de materiales que derivan en procesos complejos frente a lavados básicos.")

        col_2c, col_2d = st.columns(2)
        with col_2c:
            st.subheader("Dispersión: Colores vs Lead Time")
            fig_scatter = px.scatter(df_filtrado, x='Colores', y='Lead_Time_Dias', color='Tela', size='Total_Prendas', hover_name='OS')
            st.plotly_chart(fig_scatter, use_container_width=True)
            st.caption("Conclusión: Revela empíricamente si fraccionar pedidos en más colores impacta negativamente los tiempos de entrega al cliente.")
            
        with col_2d:
            st.subheader("Variabilidad de Entrega (Boxplot)")
            fig_box = px.box(df_filtrado, x='Tela', y='Lead_Time_Dias', color='Tela')
            st.plotly_chart(fig_box, use_container_width=True)
            st.caption("Conclusión: Evalúa la desviación estándar del Lead Time. Puntos fuera de las cajas representan retrasos atípicos graves.")

    # --- PESTAÑA 3: CALIDAD Y TIEMPOS ---
    with tab3:
        col_3a, col_3b = st.columns(2)
        with col_3a:
            st.subheader("Pareto de Defectos (80/20)")
            df_rep = df_filtrado[df_filtrado['Motivo_Reproceso'] != 'N/A'].groupby('Motivo_Reproceso')['Reprocesos'].sum().reset_index().sort_values('Reprocesos', ascending=False)
            if not df_rep.empty:
                df_rep['% Acumulado'] = df_rep['Reprocesos'].cumsum() / df_rep['Reprocesos'].sum() * 100
                fig_pareto = go.Figure()
                fig_pareto.add_trace(go.Bar(x=df_rep['Motivo_Reproceso'], y=df_rep['Reprocesos'], name='Defectos', marker_color='#0056b3'))
                fig_pareto.add_trace(go.Scatter(x=df_rep['Motivo_Reproceso'], y=df_rep['% Acumulado'], name='Acumulado %', yaxis='y2', mode='lines+markers', line=dict(color='red', width=3)))
                fig_pareto.update_layout(yaxis2=dict(overlaying='y', side='right', range=[0, 105]), showlegend=False)
                st.plotly_chart(fig_pareto, use_container_width=True)
                st.caption("Conclusión: Identifica los pocos problemas vitales que generan la mayoría de los reprocesos en la línea.")
            else:
                st.info("Sin datos de defectos.")
            
        with col_3b:
            st.subheader("Impacto de Paradas (Horas)")
            df_tm = df_filtrado[df_filtrado['Motivo_Downtime'] != 'Sin retrasos'].groupby('Motivo_Downtime')['Tiempo_Muerto_Hrs'].sum().reset_index().sort_values('Tiempo_Muerto_Hrs', ascending=True)
            if not df_tm.empty:
                fig_tm = px.bar(df_tm, x='Tiempo_Muerto_Hrs', y='Motivo_Downtime', orientation='h', text_auto='.1f')
                st.plotly_chart(fig_tm, use_container_width=True)
                st.caption("Conclusión: Cuantifica las horas perdidas por motivo, orientando las estrategias de Mantenimiento Preventivo (TPM).")
            else:
                st.info("Sin tiempos muertos.")
            
        col_3c, col_3d = st.columns(2)
        with col_3c:
            st.subheader("Demanda de Servicios")
            df_procesos = df_filtrado.groupby('Proceso').size().reset_index(name='Cantidad').sort_values('Cantidad', ascending=False)
            fig_proc = px.bar(df_procesos, x='Proceso', y='Cantidad', text_auto=True, color='Proceso')
            st.plotly_chart(fig_proc, use_container_width=True)
            st.caption("Conclusión: Proporciona la frecuencia de los procesos para optimizar las compras de productos químicos específicos.")
            
        with col_3d:
            st.subheader("Carga en Estaciones de Planchado")
            df_plancha = pd.DataFrame({
                'Estación': ['Vaporizado', 'Pretinado', 'Planchado'],
                'Horas Totales': [df_filtrado['Vaporizado_Hrs'].sum(), df_filtrado['Pretinado_Hrs'].sum(), df_filtrado['Planchado_Hrs'].sum()]
            })
            fig_plancha = px.bar(df_plancha, x='Estación', y='Horas Totales', text_auto='.1f', color='Estación')
            st.plotly_chart(fig_plancha, use_container_width=True)
            st.caption("Conclusión: Monitoreo ergonómico y laboral para asegurar un balanceo de línea adecuado en los procesos finales.")

    # --- PESTAÑA 4: FINANZAS ---
    with tab4:
        col_4a, col_4b = st.columns(2)
        with col_4a:
            st.subheader("Márgenes por Tela")
            df_fin = df_filtrado.groupby('Tela')[['Costo_Total_S/', 'Ganancia_S/']].sum().reset_index()
            fig_fin = px.bar(df_fin, x='Tela', y=['Costo_Total_S/', 'Ganancia_S/'], barmode='group')
            st.plotly_chart(fig_fin, use_container_width=True)
            st.caption("Conclusión: Compara directamente la inversión operativa requerida frente al margen neto generado por cada materia prima.")
            
        with col_4b:
            st.subheader("Evolución de Rentabilidad Mensual")
            # Cambiamos la agrupación a meses para que coincida con el nuevo filtro
            df_tendencia = df_filtrado.groupby('Periodo_Mensual')['Ganancia_S/'].sum().reset_index()
            fig_tendencia = px.line(df_tendencia, x='Periodo_Mensual', y='Ganancia_S/', markers=True)
            st.plotly_chart(fig_tendencia, use_container_width=True)
            st.caption("Conclusión: Visibilidad financiera temporal para auditar el cumplimiento presupuestal continuo.")
            
        col_4c, col_4d = st.columns(2)
        with col_4c:
            st.subheader("Costo Total vs Lead Time")
            fig_bubble = px.scatter(df_filtrado, x='Lead_Time_Dias', y='Costo_Total_S/', size='Total_Prendas', color='Tela')
            st.plotly_chart(fig_bubble, use_container_width=True)
            st.caption("Conclusión: Relaciona ineficiencias logísticas con el costo asumido. Tiempos prolongados suelen elevar costos ocultos.")
            
        with col_4d:
            st.subheader("Composición Financiera (Waterfall)")
            costo_quimico = df_filtrado['Total_Prendas'].sum() * 1.50 
            costo_op = df_filtrado['Costo_Total_S/'].sum() - costo_quimico
            ganancia = df_filtrado['Ganancia_S/'].sum()
            fig_waterfall = go.Figure(go.Waterfall(
                orientation = "v",
                measure = ["relative", "relative", "relative", "total"],
                x = ["Costo Químico", "Costo Operativo/Limpieza", "Margen de Ganancia", "Ingreso Total"],
                y = [costo_quimico, costo_op, ganancia, costo_quimico + costo_op + ganancia],
                connector = {"line":{"color":"rgb(63, 63, 63)"}}
            ))
            st.plotly_chart(fig_waterfall, use_container_width=True)
            st.caption("Conclusión: Demuestra cómo los costos individuales se escalonan hasta conformar el precio final de venta.")

    # --- PESTAÑA 5: SIMULADOR ---
    with tab5:
        st.subheader("Planificador de Cotizaciones (What-If Analysis)")
        st.markdown("Herramienta gerencial para proyectar la rentabilidad y capacidad requerida de nuevas órdenes de servicio.")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            sim_tela = st.selectbox("Seleccione Tela:", ["DENIM", "DRILL", "PPT"])
            sim_prenda = st.selectbox("Seleccione Prenda:", ["PANTALON", "CASACA", "BERMUDA", "SHORT"])
            sim_cargo = st.checkbox("¿Aplica recargo CARGO (3 min/prenda)?")
        with col_s2:
            sim_prendas = st.number_input("Total Prendas:", min_value=1, value=100)
            sim_colores = st.number_input("Cantidad de Colores (Limpiezas):", min_value=1, max_value=12, value=1)
        with col_s3:
            sim_proceso = st.selectbox("Proceso Principal:", [
                "Suavizado", "Pre Blanqueo", "Enjuague", "Teñido Directo", 
                "Teñido Reactivo", "Teñido Azufrado", "Teñido Neón", 
                "Oxidativo", "Cationizado", "Moteado", "Barrido"
            ])
            
        pesos_sim = {'PANTALON': 0.60, 'CASACA': 0.60, 'BERMUDA': 0.40, 'SHORT': 0.25}
        costos_sim = {
            'Suavizado': {'DENIM': 0.80, 'DRILL': 1.00, 'PPT': 1.20},
            'Pre Blanqueo': {'DENIM': 1.10, 'DRILL': 1.30, 'PPT': 1.50},
            'Enjuague': {'DENIM': 0.50, 'DRILL': 0.60, 'PPT': 0.70},
            'Teñido Directo': {'DENIM': 3.50, 'DRILL': 4.20, 'PPT': 4.80},
            'Teñido Reactivo': {'DENIM': 4.50, 'DRILL': 5.80, 'PPT': 6.50},
            'Teñido Azufrado': {'DENIM': 5.00, 'DRILL': 4.50, 'PPT': 5.20},
            'Teñido Neón': {'DENIM': 4.80, 'DRILL': 4.80, 'PPT': 5.50},
            'Oxidativo': {'DENIM': 2.50, 'DRILL': 2.20, 'PPT': 2.80},
            'Cationizado': {'DENIM': 2.80, 'DRILL': 2.60, 'PPT': 3.00},
            'Moteado': {'DENIM': 3.00, 'DRILL': 0.00, 'PPT': 0.00}, 
            'Barrido': {'DENIM': 2.20, 'DRILL': 0.00, 'PPT': 0.00} 
        }
        tiempos_base_sim = {'DENIM': 5.5, 'DRILL': 3.5, 'PPT': 4.5}
        
        peso_u = pesos_sim[sim_prenda]
        costo_kg = costos_sim.get(sim_proceso, {}).get(sim_tela, 0.00)
        
        if costo_kg == 0.00:
            st.error(f"Restricción técnica: El proceso de {sim_proceso} no aplica para tela {sim_tela}.")
        else:
            factor_escala = 1.75 / 3.90
            costo_unitario_escalado = (peso_u * costo_kg) * factor_escala
            costo_unitario_base = min(costo_unitario_escalado, 1.75)
            costo_proc = sim_prendas * costo_unitario_base
            
            limpiezas = sim_colores - 1 if sim_proceso != "Suavizado" else 0
            costo_limp = limpiezas * 0.15 * sim_prendas
            
            tiempo_total_estimado = tiempos_base_sim[sim_tela] + (limpiezas * (25 / 60)) + ((sim_prendas * 180 / 3600) if sim_cargo else 0)
        
            st.markdown("### Resultados de Viabilidad")
            res1, res2, res3 = st.columns(3)
            res1.metric("Costo de Operación Estimado", f"S/ {costo_proc + costo_limp:,.2f}")
            res2.metric("Carga en Máquina Requerida", f"{tiempo_total_estimado:,.1f} hrs")
            res3.metric("Distribución Promedio por Color", f"{sim_prendas / sim_colores:,.0f} uds")

    # --- PESTAÑA 6: MONITOR DE PLANTA (En Vivo) ---
    with tab6:
        st.subheader("Supervisión de Activos en Tiempo Real")
        st.markdown("Representación digital del estado operativo de las máquinas para la gestión en el piso de planta.")
        
        maquinas_estado = {f"Lavadora {i}": "Operando" if i % 3 != 0 else "Mantenimiento" for i in range(1, 13)}
        maquinas_estado.update({f"Secadora {i}": "Operando" if i % 2 != 0 else "En Setup" for i in range(1, 5)})
        
        cols = st.columns(4)
        for index, (maq, estado) in enumerate(maquinas_estado.items()):
            color = "green" if estado == "Operando" else ("orange" if estado == "En Setup" else "red")
            with cols[index % 4]:
                st.markdown(f"""
                <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px; text-align: center;">
                    <h4 style="margin:0;">{maq}</h4>
                    <p style="color: {color}; font-weight: bold; margin:0;">{estado}</p>
                </div>
                """, unsafe_allow_html=True)
        st.caption("Conclusión: Proporciona una herramienta visual de supervisión inmediata para reasignar tareas en caso de averías o cuellos de botella.")

# ==========================================
# 6. EXPORTACIÓN DE DATOS (REPORTE)
# ==========================================
st.markdown("---")
with st.expander("Consola de Datos Maestros y Exportación"):
    st.dataframe(df_filtrado, use_container_width=True)
    st.download_button("Exportar Reporte a CSV", data=df_filtrado.to_csv(index=False).encode('utf-8'), file_name='Analitica_Lavanderia.csv', mime='text/csv')