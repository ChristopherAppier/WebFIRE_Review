import streamlit as st
import pandas as pd
import numpy as np

l_col, r_col = st.columns(2, width="stretch")

r_col.write("Table")

df = pd.DataFrame({
    'first column': [1, 2, 3, 4],
    'second column': [10, 20, 30, 40]
})

r_col.dataframe(df.style.highlight_max(axis=0))

map_data = pd.DataFrame(
    np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
    columns=['lat', 'lon'])

l_col.map(map_data)

chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['a', 'b', 'c'])

r_col.line_chart(chart_data)

check = st.sidebar.checkbox('Show square calculator')

if check:
    x = st.sidebar.slider('x')  # this is a widget
    st.sidebar.write(x, 'squared is', x * x)