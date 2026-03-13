# salvar como app.py
import streamlit as st
import math

st.set_page_config(page_title="Calculadora de Cubagem", page_icon="📦")

st.title("Calculadora de Cubagem Inversa")

volume = st.number_input("Cubagem Total (m³)", min_value=0.0, format="%.3f")

if st.button("Calcular Dimensões"):
    if volume <= 0:
        st.error("Informe uma cubagem válida")
    else:
        lado = volume ** (1/3)
        st.success(
            f"Comprimento: {lado:.3f} m\n"
            f"Largura: {lado:.3f} m\n"
            f"Altura: {lado:.3f} m"
        )
