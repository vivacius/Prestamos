import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ------------------ FUNCIÓN PARA CALCULAR DEUDA (Interés Simple) ------------------
def calcular_deuda(monto, fecha_inicio, interes_mensual, abonos):
    fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    hoy = datetime.today()
    
    # Calcular los meses transcurridos
    meses_transcurridos = (hoy.year - fecha_inicio.year) * 12 + hoy.month - fecha_inicio.month
    
    # Si el préstamo tiene menos de un mes, no se aplica interés
    if meses_transcurridos < 1:
        return monto - abonos
    
    # Calcular el interés simple
    interes_total = monto * (interes_mensual / 100) * meses_transcurridos
    
    # Calcular la deuda total
    deuda_total = monto + interes_total - abonos

    return round(deuda_total, 2)

# ------------------ INICIO APP ------------------
ARCHIVO = "prestamos.csv"
COLUMNAS = ["Nombre", "Monto", "Fecha", "Interes", "Abonos", "Estado"]

# Crear archivo si no existe
if os.path.exists(ARCHIVO):
    df = pd.read_csv(ARCHIVO)
    for col in COLUMNAS:
        if col not in df.columns:
            df[col] = 0.0 if col in ["Monto", "Interes", "Abonos"] else ""
else:
    df = pd.DataFrame(columns=COLUMNAS)
    df.to_csv(ARCHIVO, index=False)

st.title("📊 Gestión de Préstamos Personales")

# ------------------ PESTAÑAS ------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Nuevo préstamo", "💰 Registrar abono", "📈 Estado de deudas", "📝 Modificar registros", "❌ Eliminar registro"])

# ------------------ NUEVO PRÉSTAMO ------------------
with tab1:
    st.header("Registrar nuevo préstamo")

    nombre = st.text_input("Nombre del cliente")
    monto = st.number_input("Monto prestado", min_value=0.0, step=1000.0)
    fecha = st.date_input("Fecha del préstamo", value=datetime.today())
    interes = st.number_input("Interés mensual (%)", min_value=0.0, max_value=100.0, value=6.0)

    if st.button("Guardar préstamo"):
        nuevo = pd.DataFrame([{
            "Nombre": nombre,
            "Monto": monto,
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Interes": interes,
            "Abonos": 0.0,
            "Estado": "Pendiente"
        }])
        df = pd.concat([df, nuevo], ignore_index=True)
        df.to_csv(ARCHIVO, index=False)
        st.success("✅ Préstamo registrado correctamente.")

# ------------------ REGISTRAR ABONO ------------------
with tab2:
    st.header("Registrar abono")

    if not df.empty:
        clientes = df[df["Estado"] != "Pagado"]["Nombre"].unique()
        cliente = st.selectbox("Selecciona un cliente", clientes)

        abono = st.number_input("Valor del abono", min_value=0.0, step=1000.0)

        if st.button("Guardar abono"):
            index = df[df["Nombre"] == cliente].index[-1]
            df.at[index, "Abonos"] += abono
            # Recalcular deuda
            row = df.loc[index]
            deuda = calcular_deuda(row["Monto"], row["Fecha"], row["Interes"], row["Abonos"])
            if deuda <= 0:
                df.at[index, "Estado"] = "Pagado"
            df.to_csv(ARCHIVO, index=False)
            st.success("💸 Abono registrado correctamente.")
    else:
        st.warning("No hay clientes registrados aún.")

# ------------------ ESTADO DE DEUDAS ------------------
with tab3:
    st.header("Resumen de préstamos")

    if df.empty:
        st.info("No hay registros aún.")
    else:
        # Limpiar las comas y convertir a float de manera segura
        df["Monto"] = df["Monto"].apply(lambda x: float(str(x).replace(',', '').replace(' ', '')))
        df["Abonos"] = df["Abonos"].apply(lambda x: float(str(x).replace(',', '').replace(' ', '')))

        # Calcular la deuda sin formatear para evitar el error de conversión
        df["Deuda_actual"] = df.apply(
            lambda row: calcular_deuda(row["Monto"], row["Fecha"], row["Interes"], row["Abonos"]),
            axis=1
        )

        # Mostrar los montos sin formato
        st.dataframe(df)

        # Calcular el total de deuda por cobrar sin formatear
        total_deuda = df[df["Estado"] != "Pagado"]["Deuda_actual"].sum()

        # Mostrar el total por cobrar
        st.metric("💰 Total por cobrar", f"{total_deuda:,.0f}")

# ------------------ MODIFICAR REGISTRO ------------------
with tab4:
    st.header("Modificar registros")

    if not df.empty:
        clientes = df["Nombre"].unique()
        cliente_a_modificar = st.selectbox("Selecciona el cliente a modificar", clientes)

        # Seleccionar el índice del cliente
        index = df[df["Nombre"] == cliente_a_modificar].index[-1]

        # Mostrar los detalles del cliente seleccionado
        cliente = df.loc[index]

        # Convertir a número para evitar el error de conversión
        monto_nuevo = st.number_input("Nuevo monto prestado", value=cliente["Monto"], min_value=0.0, step=1000.0)
        fecha_nueva = st.date_input("Nueva fecha de préstamo", value=datetime.strptime(cliente["Fecha"], "%Y-%m-%d"))
        interes_nuevo = st.number_input("Nuevo interés mensual (%)", value=cliente["Interes"], min_value=0.0, max_value=100.0)

        # Opción para eliminar abonos
        abonos_existentes = cliente["Abonos"]
        eliminar_abono = st.checkbox(f"Eliminar abono de {abonos_existentes}")

        if st.button("Guardar cambios"):
            if eliminar_abono:
                df.at[index, "Abonos"] = 0.0  # Eliminar los abonos
            else:
                df.at[index, "Abonos"] = abonos_existentes  # Mantener los abonos actuales

            df.at[index, "Monto"] = monto_nuevo
            df.at[index, "Fecha"] = fecha_nueva.strftime("%Y-%m-%d")
            df.at[index, "Interes"] = interes_nuevo

            # Recalcular deuda
            deuda = calcular_deuda(df.loc[index]["Monto"], df.loc[index]["Fecha"], df.loc[index]["Interes"], df.loc[index]["Abonos"])
            if deuda <= 0:
                df.at[index, "Estado"] = "Pagado"
            df.to_csv(ARCHIVO, index=False)
            st.success("📝 Registro modificado correctamente.")
    else:
        st.warning("No hay registros para modificar.")

# ------------------ ELIMINAR REGISTRO ------------------
with tab5:
    st.header("Eliminar registro")

    if not df.empty:
        clientes = df["Nombre"].unique()
        cliente_a_eliminar = st.selectbox("Selecciona el cliente a eliminar", clientes)

        if st.button("Eliminar cliente"):
            # Seleccionar el índice del cliente
            index = df[df["Nombre"] == cliente_a_eliminar].index[-1]
            df = df.drop(index)  # Eliminar el registro

            # Guardar los cambios en el archivo CSV
            df.to_csv(ARCHIVO, index=False)
            st.success(f"✅ El cliente {cliente_a_eliminar} ha sido eliminado correctamente.")
    else:
        st.warning("No hay registros para eliminar.")
