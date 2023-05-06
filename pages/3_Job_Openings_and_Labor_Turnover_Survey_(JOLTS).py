import streamlit as st
import pandas as pd

from functions import init_connection

@st.cache_resource
def load_state_employment_data():
    cur.execute("SELECT TS.VARIABLE, VALUE, DATE, MEASURE, INDUSTRY, GEO.ID, GEO.GEO_NAME "
                    + "FROM BLS_EMPLOYMENT_TIMESERIES AS TS "
                    + "JOIN BLS_EMPLOYMENT_ATTRIBUTES AS ATT ON (TS.VARIABLE = ATT.VARIABLE) "
                    + "JOIN BLS_GEO_INDEX AS GEO ON (TS.GEO_ID = GEO.ID) "
                    + "WHERE GEO.LEVEL = 'State' AND ATT.UNIT = 'Level' AND REPORT = 'JOLTS' AND FREQUENCY = 'Annual' "
                    + "ORDER BY GEO_NAME, DATE")
    return cur.fetch_pandas_all()

conn = init_connection()
cur = conn.cursor()

st.header('Job Openings and Labor Turnover Survey (JOLTS)')
st.write('This chart below shows the comparision in the number of Hires, Layoffs & Discharges, Job Openings, Quits and Other Separations of a selected year among states in the US.')


state_employment_df = load_state_employment_data()
state_employment_df['YEAR'] = pd.DatetimeIndex(state_employment_df['DATE']).year
state_employment_df['GEO_ID'] = state_employment_df['ID'].str.split('/').str[1].astype(int)
state_employment_df = state_employment_df.filter(items=['VALUE', 'MEASURE', 'GEO_NAME', 'GEO_ID', 'YEAR'])

selected_year = st.selectbox('Select year', state_employment_df['YEAR'].unique())
if (selected_year):
    state_employment_selected_year_df = state_employment_df[state_employment_df['YEAR'] == selected_year]
    state_employment_selected_year_df = state_employment_selected_year_df.drop(['YEAR'], axis=1)
    table = pd.pivot_table(state_employment_selected_year_df, index=['GEO_ID', 'GEO_NAME'], columns=['MEASURE'])
    table.columns = ['_'.join(str(s).strip() for s in col if s) for col in table.columns]
    table.rename(columns={
        "VALUE_Hires": "Hires", 
        "VALUE_Job openings": "Job openings", 
        "VALUE_Layoffs and discharges": "Layoffs and discharges",
        "VALUE_Quits": "Quits",
        "VALUE_Total separations": "Total separations",
    }, inplace=True)
    table.reset_index(inplace=True)
    table['Other separations'] = table['Total separations'] - table['Quits'] - table['Layoffs and discharges']

    tab1, tab2 = st.tabs(["Chart", "Data"])
    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            chart = {
                "width": 600,
                "height": 400,
                "data": {
                    "url": "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json",
                    "format": {"type": "topojson", "feature": "states"}
                },
                "transform": [{
                    "lookup": "id",
                    "from": {"data": {"name": "source"}, "key": "GEO_ID", "fields": ["Hires"]}
                }],
                "projection": {
                    "type": "albersUsa"
                },
                "mark": "geoshape",
                "encoding": {
                    "color": {
                    "field": "Hires",
                    "type": "quantitative"
                    }
                }
            }
            st.vega_lite_chart(table, chart)

            chart = {
                "width": 600,
                "height": 400,
                "data": {
                    "url": "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json",
                    "format": {"type": "topojson", "feature": "states"}
                },
                "transform": [{
                    "lookup": "id",
                    "from": {"data": {"name": "source"}, "key": "GEO_ID", "fields": ["Job openings"]}
                }],
                "projection": {
                    "type": "albersUsa"
                },
                "mark": "geoshape",
                "encoding": {
                    "color": {
                    "field": "Job openings",
                    "type": "quantitative"
                    }
                }
            }
            st.vega_lite_chart(table, chart)

            chart = {
                "width": 600,
                "height": 400,
                "data": {
                    "url": "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json",
                    "format": {"type": "topojson", "feature": "states"}
                },
                "transform": [{
                    "lookup": "id",
                    "from": {"data": {"name": "source"}, "key": "GEO_ID", "fields": ["Other separations"]}
                }],
                "projection": {
                    "type": "albersUsa"
                },
                "mark": "geoshape",
                "encoding": {
                    "color": {
                    "field": "Other separations",
                    "type": "quantitative"
                    }
                }
            }
            st.vega_lite_chart(table, chart)
        
        with col2:
            chart = {
                "width": 600,
                "height": 400,
                "data": {
                    "url": "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json",
                    "format": {"type": "topojson", "feature": "states"}
                },
                "transform": [{
                    "lookup": "id",
                    "from": {"data": {"name": "source"}, "key": "GEO_ID", "fields": ["Layoffs and discharges"]}
                }],
                "projection": {
                    "type": "albersUsa"
                },
                "mark": "geoshape",
                "encoding": {
                    "color": {
                    "field": "Layoffs and discharges",
                    "type": "quantitative"
                    }
                }
            }
            st.vega_lite_chart(table, chart)

            chart = {
                "width": 600,
                "height": 400,
                "data": {
                    "url": "https://cdn.jsdelivr.net/npm/vega-datasets@v1.29.0/data/us-10m.json",
                    "format": {"type": "topojson", "feature": "states"}
                },
                "transform": [{
                    "lookup": "id",
                    "from": {"data": {"name": "source"}, "key": "GEO_ID", "fields": ["Quits"]}
                }],
                "projection": {
                    "type": "albersUsa"
                },
                "mark": "geoshape",
                "encoding": {
                    "color": {
                    "field": "Quits",
                    "type": "quantitative"
                    }
                }
            }
            st.vega_lite_chart(table, chart)
            

    with tab2:
        st.dataframe(table)

    
    