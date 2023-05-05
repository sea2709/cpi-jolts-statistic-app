import streamlit as st
import snowflake.connector

@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )

def build_category_cpi_df(cpi_df, key, variable, filterByYear = True, filterByMonth = False):
    df = cpi_df[cpi_df['VARIABLE'] == variable];
    df[key] = df['VALUE']

    if (filterByYear):
        df = df.filter(items=[key, 'YEAR'])
        df.set_index('YEAR', inplace=True)

    if (filterByMonth):
        df = df.filter(items=[key, 'MONTH'])
        df.set_index('MONTH', inplace=True)

    return df