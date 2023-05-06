import streamlit as st
import pandas as pd
import datetime

from datetime import date
from functions import init_connection

@st.cache_resource
def load_industries():
    cur.execute("SELECT DISTINCT(INDUSTRY) FROM BLS_EMPLOYMENT_ATTRIBUTES WHERE INDUSTRY NOT LIKE '%:%'")
    return cur.fetch_pandas_all()

@st.cache_resource
def load_metro_areas():
    cur.execute("SELECT GEO_NAME FROM BLS_GEO_INDEX WHERE LEVEL = 'CensusCoreBasedStatisticalArea' AND GEO_NAME LIKE '%Metro Area'")
    return cur.fetch_pandas_all()

def load_state_metro_employment_by_industries(industries, min_date):
    sql_list = str(tuple([key for key in industries])).replace(',)', ')')
    cur.execute("SELECT geo.geo_name, att.industry, ts.date, ts.value "
        + "FROM bls_employment_timeseries AS ts "
        + "JOIN bls_employment_attributes AS att ON (ts.variable = att.variable) "
        + "JOIN bls_geo_index AS geo ON (ts.geo_id = geo.id) "
        + "WHERE att.report = 'State and Metro Employment' "
        + f"AND att.industry IN {sql_list} "
        + "AND att.measure = 'All Employees' "
        + "AND att.frequency = 'Monthly' "
        + "AND att.seasonally_adjusted = FALSE "
        + "AND geo.level = 'CensusCoreBasedStatisticalArea' "
        + f"AND DATE >= '{min_date}' "
        + "ORDER BY date")

    
    return cur.fetch_pandas_all()

conn = init_connection()
cur = conn.cursor()

st.header('State and Metro Employment')
st.write('These charts below show the total count of employees in selected industries in specific metro areas through 12 months.')
industries = load_industries()
metro_areas = load_metro_areas()

col1, col2 = st.columns(2)

selected_industries = col1.multiselect('Select industries', industries, default=['Financial Activities', 'Government', 'Information'])
if (selected_industries):
    selected_areas = col2.multiselect('Select metro areas', metro_areas, default=['Dallas-Fort Worth-Arlington, TX Metro Area', 'New York-Newark-Jersey City, NY-NJ-PA Metro Area'])
    if (selected_areas):
        today = date.today()
        employment_df = load_state_metro_employment_by_industries(selected_industries, datetime.datetime(today.year - 1, today.month, 1))
        employment_df['MONTH'] = pd.DatetimeIndex(employment_df['DATE']).strftime('%Y-%m')

        for area in selected_areas:
            with st.expander(area):
                df = employment_df[employment_df['GEO_NAME'] == area]
                tab1, tab2 = st.tabs(["Chart", "Data"])
                tab2.dataframe(df)
                chart = {
                    "mark": "bar",
                    "encoding": {
                        "x": {"field": "MONTH"},
                        "y": {"field": "VALUE", "type": "quantitative"},
                        "xOffset": {"field": "INDUSTRY"},
                        "color": {"field": "INDUSTRY"}
                    }
                }
                tab1.vega_lite_chart(df, chart, use_container_width=True)