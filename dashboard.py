# Immportamos librerias:
import pandas as pd
import numpy as np
import matplotlib as plt
import streamlit as st
import plotly.express as px

# LECTURA ARCHIVOS =======================================================================
# Datos
data=pd.read_csv('https://raw.githubusercontent.com/pablollanten/dashboardBi/refs/heads/master/actualBudget.csv',
                 sep=';')

# Plan de cuentas
coa=pd.read_csv('https://raw.githubusercontent.com/pablollanten/dashboardBi/refs/heads/master/coa.csv',
                sep=';')

# Chequeando nulos
data.isnull().sum()
coa.isnull().sum()

# EDA ===================================================================================
# Fusionamos los data frames de los valores y el plan de cuentas
data=pd.merge(data,coa,on='cuenta',how='left')

# Cambio el tipo de dato de la columna fecha a dd-mm-aaaa
data['fecha'] = pd.to_datetime(data['fecha'], format='%d/%m/%Y')

# Renombrar columna monto
data = data.rename(columns={'monto': 'CLP'})

# Creo nueva columna con nombre de los productos:
data['Producto']=np.where(data['codProducto']==390,'Botellones',
                          np.where(data['codProducto']==400,'TambCilindrico',
                                   np.where(data['codProducto']==450,'TambConico',
                                            'Miscelaneo')
                          )
                          )

# Creo columna para el mes
data['mes']=data['fecha'].dt.month

# Creo columna para el año
data['año']=data['fecha'].dt.year

# Creo una columna con monto en millones
data['MM CLP']=round(data['CLP']/1000000,2)

# Creo nueva columna para identificar los trimestres
data['Trimestre']=np.where((data['mes']>=1) & (data['mes']<=3),'Q1',
                          np.where((data['mes']>=4) & (data['mes']<=6),'Q2',
                                   np.where((data['mes']>=7) & (data['mes']<=9),'Q3',
                                            'Q4')
                          )
                          )

# METRICAS =========================================================================================

# VENTAS
ventas=data[data['grupo1'] == 'Ventas'].groupby(['Producto','escenario', 'año', 'mes', 'Trimestre'])['MM CLP'].sum().reset_index()

# COGS, VOH Y FOH
costoVaryFijo=data.loc[(data['grupo1']=="COGS")|(data['grupo1']=="Transporte")|(data['grupo1']=="VariableOH")|(data['grupo1']=="FixedOH")].groupby(['Producto','escenario', 'año', 'mes', 'Trimestre'])['MM CLP'].sum().reset_index()

# SGA
sga=data[data['grupo1'] == 'SGA'].groupby(['Producto','escenario', 'año', 'mes', 'Trimestre'])['MM CLP'].sum().reset_index()

# CONTRIBUCION
# fusionamos ventas y costos
contribucion=pd.merge(ventas, costoVaryFijo,on=['Producto', 'escenario', 'año', 'mes', 'Trimestre'],how='left')

# Calculamos la contribucion
contribucion['MM CLP']=round(contribucion['MM CLP_x']-contribucion['MM CLP_y'],2)

# Eliminamos columnas q no necesitamos
contribucion = contribucion.drop(['MM CLP_x', 'MM CLP_y'], axis=1)

# EBITDA
# fusionamos Contribucion y SGA
ebitda=pd.merge(contribucion, sga,on=['Producto', 'escenario', 'año', 'mes', 'Trimestre'],how='left')

# Calculamos el EBITDA
ebitda['MM CLP']=round(ebitda['MM CLP_x']-ebitda['MM CLP_y'],2)

# Eliminamos columnas q no necesitamos
ebitda= ebitda.drop(['MM CLP_x', 'MM CLP_y'], axis=1)

# Listado de prouctos unicos para filtros:
linProducto=list(ventas['Producto'].unique())
linProducto.append('Todos')

# UNIDADES
# Unidades de venta:
unidsVenta=data[data['descripcion']=='Unids_Venta'].groupby(['Producto','escenario', 'año', 'mes', 'Trimestre'])['MM CLP'].sum().reset_index()

# Unids de produccion:
unidsProd=data[data['descripcion']=='Unids_Prod'].groupby(['Producto','escenario', 'año', 'mes', 'Trimestre'])['MM CLP'].sum().reset_index()

# Corregimos nombre de la columna unidades
unidsVenta = unidsVenta.rename(columns={'MM CLP':'M Unids'})
unidsProd = unidsProd.rename(columns={'MM CLP':'M Unids'})

# Corregimos miles en columna unidades
unidsVenta['M Unids']=unidsVenta['M Unids']*1000

unidsProd['M Unids']=unidsProd['M Unids']*1000

# Incoproramos precio unitario
ventas=pd.merge(ventas, unidsVenta,on=['Producto', 'escenario', 'año', 'mes', 'Trimestre'],how='left')

# Calculamos el precio unitario
ventas['precioUnitario']=round(ventas['MM CLP']/(ventas['M Unids']/1000),2)

# Botamos la columna quw no sirve
ventas=ventas.drop(['M Unids'], axis=1)

# Incoproramos costo unitario
costoVaryFijo=pd.merge(costoVaryFijo, unidsVenta,on=['Producto', 'escenario', 'año', 'mes', 'Trimestre'],how='left')

# Calculamos el costo unitario
costoVaryFijo['costoUnitario']=round(costoVaryFijo['MM CLP']/(costoVaryFijo['M Unids']/1000),2)

# Botamos la columna quw no sirve
costoVaryFijo=costoVaryFijo.drop(['M Unids'], axis=1)

# Contribucion unitaria
# Agregamos el precio unitario
contribucion=pd.merge(contribucion, unidsVenta, on=['Producto', 'escenario', 'año', 'mes', 'Trimestre'],how='left')

# Calculamos la contribucion unitario
contribucion['contrUnitaria']=round(contribucion['MM CLP']/(contribucion['M Unids']/1000),2)

# Botamos la columna quw no sirve
contribucion =contribucion.drop(['M Unids'], axis=1)


# =====================DASHBOARD==========================================================================
# CONFIGURACION DE LA PAGINA =============================================================================
st.set_page_config(
    page_title="Greif", # Titulo de la pestaña
    page_icon="\U0001F600", # favicon
    layout='wide',
    initial_sidebar_state='expanded'
)

# Titulo del dashboard:
st.markdown('<h1 class="main header"> Dashboard de prueba para Greif </h1>', 
            unsafe_allow_html=True)

# Columnas filtro del dashboard en cabeceras:
col1, col2, col3=st.columns(3)
with col1:
    periodo=st.selectbox("Periodo (mes)",
                         list(ventas['mes'].unique())) # Genero una lista con los meses en numero
with col2:
    producto=st.selectbox("Producto", 
                          linProducto) # Lienea de producto a filtrar
with col3:
    comparacion=st.selectbox("Comparación",
                         ["Budget", "Año Anterior"]) # Deshabilitado porque no hay datos de ano anterior

st.markdown('KPIs')
col1, col2, col3, col4=st.columns(4)

# KPIS =============================================================================================
# VENTAS MES
with col1:
    if producto!='Todos': # condicion para tomar todos los productos
        st.metric(label='Revenues Periodo KUSD', 
                  value=f'${ventas[(ventas['mes']==periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
                  delta=f'{ventas[(ventas['mes']==periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='actuals')]['MM CLP'].sum()-
                           ventas[(ventas['mes']==periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                           )    
    else:
        st.metric(label='Revenues Periodo KUSD', 
              value=f'${ventas[(ventas['mes']==periodo) & (ventas['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
              delta=f'{ventas[(ventas['mes']==periodo) & (ventas['escenario']=='actuals')]['MM CLP'].sum()-
                       ventas[(ventas['mes']==periodo) & (ventas['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                       )

 # VENTAS YTD  
with col2:
    if producto!='Todos':
        st.metric(label='Revenues YTD KUSD',
                  value=f'${ventas[(ventas['mes']<=periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
                  delta=f'{ventas[(ventas['mes']<=periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='actuals')]['MM CLP'].sum()-
                           ventas[(ventas['mes']<=periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                           )
    else:
        st.metric(label='Revenues YTD KUSD',
                  value=f'${ventas[(ventas['mes']<=periodo) & (ventas['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
                  delta=f'{ventas[(ventas['mes']<=periodo) & (ventas['escenario']=='actuals')]['MM CLP'].sum()-
                           ventas[(ventas['mes']<=periodo) & (ventas['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                           )

# KPI 3: EBITDA PERIODO    
with col3:
    if producto!='Todos':
        st.metric(label='Ebitda Periodo KUSD',
                  value=f'${ebitda[(ebitda['mes']==periodo) & (ebitda['Producto']==producto) & (ebitda['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
                  delta=f'{ebitda[(ebitda['mes']==periodo) & (ebitda['Producto']==producto) & (ebitda['escenario']=='actuals')]['MM CLP'].sum()-
                           ebitda[(ebitda['mes']==periodo) & (ebitda['Producto']==producto) & (ebitda['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                           )
    else:
        st.metric(label='Ebitda Periodo KUSD',
                  value=f'${ebitda[(ebitda['mes']==periodo) & (ebitda['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
                  delta=f'{ebitda[(ebitda['mes']==periodo) & (ebitda['escenario']=='actuals')]['MM CLP'].sum()-
                           ebitda[(ebitda['mes']==periodo) & (ebitda['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                           )

# KPI 4: EBITDA YTD
with col4:
    if producto!='Todos':
        st.metric(label='Ebitda YTD KUSD',
                  value=f'${ebitda[(ebitda['mes']<=periodo) & (ebitda['Producto']==producto) & (ebitda['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
                  delta=f'{ebitda[(ebitda['mes']<=periodo) & (ebitda['Producto']==producto) & (ebitda['escenario']=='actuals')]['MM CLP'].sum()-
                           ebitda[(ebitda['mes']<=periodo) & (ebitda['Producto']==producto) & (ebitda['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                           )
    else:
        st.metric(label='Ebitda YTD KUSD',
                  value=f'${ebitda[(ebitda['mes']<=periodo) & (ebitda['escenario']=='actuals')]['MM CLP'].sum():,.0f}',
                  delta=f'{ebitda[(ebitda['mes']<=periodo) & (ebitda['escenario']=='actuals')]['MM CLP'].sum()-
                           ebitda[(ebitda['mes']<=periodo) & (ebitda['escenario']=='budget')]['MM CLP'].sum():,.0f}'
                           )

# UNIDADES - PRECIOS
st.markdown("Unidades y Precios Unitarios")
col1, col2, col3, col4= st.columns(4)

# UNIDS VENTA MES
with col1:
    if producto!='Todos':
        st.metric(label='Uds Vta Mes MU',
                  value=f'{unidsVenta[(unidsVenta['mes']==periodo) & (unidsVenta['Producto']==producto) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum():,.0f}',
                  delta=f'{unidsVenta[(unidsVenta['mes']==periodo) & (unidsVenta['Producto']==producto) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum()-
                           unidsVenta[(unidsVenta['mes']==periodo) & (unidsVenta['Producto']==producto) & (unidsVenta['escenario']=='budget')]['M Unids'].sum():,.0f}'
                           )
    else:
        st.metric(label='Uds Vta Mes MU ',
                  value=f'{unidsVenta[(unidsVenta['mes']==periodo) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum():,.0f}',
                  delta=f'{unidsVenta[(unidsVenta['mes']==periodo) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum()-
                           unidsVenta[(unidsVenta['mes']==periodo) & (unidsVenta['escenario']=='budget')]['M Unids'].sum():,.0f}'
                           )

# UNIDS VENTA YTD
with col2:
    if producto!='Todos':
        st.metric(label='Uds Vta YTD MU',
                  value=f'{unidsVenta[(unidsVenta['mes']<=periodo) & (unidsVenta['Producto']==producto) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum():,.0f}',
                  delta=f'{unidsVenta[(unidsVenta['mes']<=periodo) & (unidsVenta['Producto']==producto) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum()-
                           unidsVenta[(unidsVenta['mes']<=periodo) & (unidsVenta['Producto']==producto) & (unidsVenta['escenario']=='budget')]['M Unids'].sum():,.0f}'
                           )
    else:
        st.metric(label='Uds Vta YTD MU',
                  value=f'{unidsVenta[(unidsVenta['mes']<=periodo) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum():,.0f}',
                  delta=f'{unidsVenta[(unidsVenta['mes']<=periodo) & (unidsVenta['escenario']=='actuals')]['M Unids'].sum()-
                           unidsVenta[(unidsVenta['mes']<=periodo) & (unidsVenta['escenario']=='budget')]['M Unids'].sum():,.0f}'
                           )
        
# UNIDS PROD YTD
with col3:
    if producto!='Todos':
        st.metric(label='Uds Prod YTD MU',
                  value=f'{unidsProd[(unidsProd['mes']<=periodo) & (unidsProd['Producto']==producto) & (unidsProd['escenario']=='actuals')]['M Unids'].sum():,.0f}',
                  delta=f'{unidsProd[(unidsProd['mes']<=periodo) & (unidsProd['Producto']==producto) & (unidsProd['escenario']=='actuals')]['M Unids'].sum()-
                           unidsProd[(unidsProd['mes']<=periodo) & (unidsProd['Producto']==producto) & (unidsProd['escenario']=='budget')]['M Unids'].sum():,.0f}'
                           )
    else:
        st.metric(label='Uds Prod YTD MU',
                  value=f'{unidsProd[(unidsProd['mes']<=periodo) & (unidsProd['escenario']=='actuals')]['M Unids'].sum():,.0f}',
                  delta=f'{unidsProd[(unidsProd['mes']<=periodo) & (unidsProd['escenario']=='actuals')]['M Unids'].sum()-
                           unidsProd[(unidsProd['mes']<=periodo) & (unidsProd['escenario']=='budget')]['M Unids'].sum():,.0f}'
                           )
        
# PRECIO MEDIO VENTA
with col4:
    if producto!='Todos':
        st.metric(label='PU Medio Venta YTD',
                  value=f'${ventas[(ventas['mes']<=periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='actuals')]['precioUnitario'].mean()/1000:,.0f}',
                  delta=f'{ventas[(ventas['mes']<=periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='actuals')]['precioUnitario'].mean()/1000 -
                           ventas[(ventas['mes']<=periodo) & (ventas['Producto']==producto) & (ventas['escenario']=='budget')]['precioUnitario'].mean()/1000 :,.0f}'
                           )
    else:
        st.metric(label='PU Medio Venta YTD',
                  value=f'${ventas[(ventas['mes']<=periodo) & (ventas['escenario']=='actuals')]['precioUnitario'].mean()/1000:,.0f}',
                  delta=f'{ventas[(ventas['mes']<=periodo) & (ventas['escenario']=='actuals')]['precioUnitario'].mean()/1000 -
                           ventas[(ventas['mes']<=periodo) & (ventas['escenario']=='budget')]['precioUnitario'].mean()/1000 :,.0f}'
                           )

# GRAFICOS ==========================================================================================
st.markdown("Tendencias")
col1, col2= st.columns(2)

# VENTAS VS BUDGET ACUMULADO
with col1:
    if producto!='Todos':
        ventasBudget= ventas[(ventas['escenario'] == 'budget') & (ventas['Producto'] == producto)].copy()
        ventasBudget= ventasBudget.sort_values(by='mes')
        ventasBudget['MM CLP_acumulado'] = ventasBudget['MM CLP'].cumsum()

        ventasActuals=ventas[(ventas['escenario'] == 'actuals') & (ventas['Producto'] == producto) & (ventas['mes'] <= periodo)].copy()
        ventasActuals= ventasActuals.sort_values(by='mes')
        ventasActuals['MM CLP_acumulado'] = ventasActuals['MM CLP'].cumsum()

        ventasCombinadas=pd.concat([ventasActuals, ventasBudget])

        fig = px.line(
            ventasCombinadas,
            x='mes',
            y='MM CLP_acumulado',
            color='escenario', # Diferenciar las líneas por escenario
            title='Ventas Acumuladas (Budget vs Real) por Mes',
            labels={'mes': 'Mes', 'MM CLP_acumulado': 'K USD Acumulados'},
            markers=True
            )
        st.plotly_chart(fig, use_container_width=True)

    else:
        ventasBudget= ventas[(ventas['escenario'] == 'budget')].copy()
        ventasBudget= ventasBudget.groupby(['mes', 'escenario', 'año', 'Trimestre'])['MM CLP'].sum()
        
        ventasActuals= ventas[(ventas['escenario'] == 'actuals') & (ventas['mes'] <= periodo)].copy()
        ventasActuals= ventasActuals.groupby(['mes', 'escenario', 'año', 'Trimestre'])['MM CLP'].sum()

        ventasCombinadas=pd.concat([ventasActuals, ventasBudget]).reset_index()

        ventasCombinadas = ventasCombinadas.sort_values(by=['escenario', 'año', 'mes'])
        ventasCombinadas['MM CLP_acumulado'] = ventasCombinadas.groupby(['escenario', 'año'])['MM CLP'].cumsum()

        fig = px.line(
            ventasCombinadas,
            x='mes',
            y='MM CLP_acumulado',
            color='escenario',
            title='Ventas Acumuladas (Budget vs Real) por Mes',
            labels={'mes': 'Mes', 'MM CLP_acumulado': 'K USD Acumulados'},
            markers=True
            )
        st.plotly_chart(fig, use_container_width=True)

# EBITDA VS BUDGET ACUMULADO
with col2:
    if producto!='Todos':
        ebitdaBudget= ebitda[(ebitda['escenario'] == 'budget') & (ebitda['Producto'] == producto)].copy()
        ebitdaBudget= ebitdaBudget.sort_values(by='mes')
        ebitdaBudget['MM CLP_acumulado'] = ebitdaBudget['MM CLP'].cumsum()

        ebitdaActuals=ebitda[(ebitda['escenario'] == 'actuals') & (ebitda['Producto'] == producto) & (ebitda['mes'] <= periodo)].copy()
        ebitdaActuals= ebitdaActuals.sort_values(by='mes')
        ebitdaActuals['MM CLP_acumulado'] = ebitdaActuals['MM CLP'].cumsum()

        ebitdaCombinado=pd.concat([ebitdaActuals, ebitdaBudget])

        fig = px.line(
            ebitdaCombinado,
            x='mes',
            y='MM CLP_acumulado',
            color='escenario', # Diferenciar las líneas por escenario
            title='Ebitda Acumulado (Budget vs Real) por Mes',
            labels={'mes': 'Mes', 'MM CLP_acumulado': 'K USD Acumulados'},
            markers=True
            )
        st.plotly_chart(fig, use_container_width=True)

    else:
        ebitdaBudget= ebitda[(ebitda['escenario'] == 'budget')].copy()
        ebitdaBudget= ebitdaBudget.groupby(['mes', 'escenario', 'año', 'Trimestre'])['MM CLP'].sum()
        
        ebitdaActuals= ebitda[(ebitda['escenario'] == 'actuals') & (ventas['mes'] <= periodo)].copy()
        ebitdaActuals= ebitdaActuals.groupby(['mes', 'escenario', 'año', 'Trimestre'])['MM CLP'].sum()

        ebitdaCombinado=pd.concat([ebitdaActuals, ebitdaBudget]).reset_index()

        ebitdaCombinado = ebitdaCombinado.sort_values(by=['escenario', 'año', 'mes'])
        ebitdaCombinado['MM CLP_acumulado'] = ebitdaCombinado.groupby(['escenario', 'año'])['MM CLP'].cumsum()

        fig = px.line(
            ebitdaCombinado,
            x='mes',
            y='MM CLP_acumulado',
            color='escenario',
            title='Ebitda Acumulado (Budget vs Real) por Mes',
            labels={'mes': 'Mes', 'MM CLP_acumulado': 'K USD Acumulados'},
            markers=True
            )
        st.plotly_chart(fig, use_container_width=True)


