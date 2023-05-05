import streamlit as st
import pandas as pd
import datetime

from datetime import date
from functions import init_connection, build_category_cpi_df

@st.cache_resource
def get_max_date_in_data():
    d = cur.execute("select max(DATE) FROM BLS_EMPLOYMENT_TIMESERIES").fetchone()
    return d[0]

@st.cache_resource
def load_cpi_data_from(selected_date):
    cur.execute("SELECT GEO_ID,  GEO_NAME, ts.VARIABLE, ts.VARIABLE_NAME, PRODUCT, VALUE, LEVEL, DATE "
        + "FROM cybersyn.bls_price_timeseries AS ts "
        + "JOIN cybersyn.bls_price_attributes AS att ON (ts.variable = att.variable) "
        + "JOIN cybersyn.bls_geo_index AS geo ON (ts.geo_id = geo.id) "
        + "WHERE att.report = 'Consumer Price Index' "
        + f"AND ts.date >= '{selected_date}' "
        + "AND ts.VARIABLE IN ('CPI:_All_items,_Not_seasonally_adjusted,_Monthly', 'CPI:_Energy,_Not_seasonally_adjusted,_Monthly', 'CPI:_Food,_Not_seasonally_adjusted,_Monthly', 'CPI:_All_items_less_food_and_energy,_Not_seasonally_adjusted,_Monthly') "
        + "ORDER BY date")

    return cur.fetch_pandas_all()

conn = init_connection()
cur = conn.cursor()

max_date = get_max_date_in_data()
last_year_date = datetime.date(max_date.year - 1, max_date.month - 1, 1)
twelve_month_cpi_df = load_cpi_data_from(last_year_date)
twelve_month_cpi_df['MONTH'] = pd.DatetimeIndex(twelve_month_cpi_df['DATE']).strftime('%Y-%m')

twelve_month_cpi_df = twelve_month_cpi_df[twelve_month_cpi_df['GEO_ID'] == 'country/USA']

food_df = build_category_cpi_df(twelve_month_cpi_df, 'FOOD', 'CPI:_Food,_Not_seasonally_adjusted,_Monthly', filterByYear=False, filterByMonth=True)
all_items_df = build_category_cpi_df(twelve_month_cpi_df, 'ALL ITEMS', 'CPI:_All_items,_Not_seasonally_adjusted,_Monthly', filterByYear=False, filterByMonth=True)
energy_df = build_category_cpi_df(twelve_month_cpi_df, 'ENERGY', 'CPI:_Energy,_Not_seasonally_adjusted,_Monthly', filterByYear=False, filterByMonth=True)
all_items_less_food_and_energy_df = build_category_cpi_df(twelve_month_cpi_df, 'ALL ITEMS LESS FOOD AND ENERGY', 'CPI:_All_items_less_food_and_energy,_Not_seasonally_adjusted,_Monthly', filterByYear=False, filterByMonth=True)

main_categories_cpi_df = pd.merge(left=all_items_df, right=food_df, how='outer', left_index=True, right_index=True)
main_categories_cpi_df = main_categories_cpi_df.merge(energy_df, how='outer', left_index=True, right_index=True)
main_categories_cpi_df = main_categories_cpi_df.merge(all_items_less_food_and_energy_df, how='outer', left_index=True, right_index=True)
main_categories_cpi_df.reset_index(inplace=True)
for i in range(1, len(main_categories_cpi_df)):
    main_categories_cpi_df.loc[i, 'ALL ITEMS PERCENTAGE'] = (main_categories_cpi_df.loc[i, 'ALL ITEMS'] - main_categories_cpi_df.loc[i - 1, 'ALL ITEMS']) / main_categories_cpi_df.loc[i - 1, 'ALL ITEMS'] * 100
    main_categories_cpi_df.loc[i, 'FOOD PERCENTAGE'] = (main_categories_cpi_df.loc[i, 'FOOD'] - main_categories_cpi_df.loc[i - 1, 'FOOD']) / main_categories_cpi_df.loc[i - 1, 'FOOD'] * 100
    main_categories_cpi_df.loc[i, 'ENERGY PERCENTAGE'] = (main_categories_cpi_df.loc[i, 'ENERGY'] - main_categories_cpi_df.loc[i - 1, 'ENERGY']) / main_categories_cpi_df.loc[i - 1, 'ENERGY'] * 100
    main_categories_cpi_df.loc[i, 'ALL ITEMS LESS FOOD AND ENERGY PERCENTAGE'] = (main_categories_cpi_df.loc[i, 'ALL ITEMS LESS FOOD AND ENERGY'] - main_categories_cpi_df.loc[i - 1, 'ALL ITEMS LESS FOOD AND ENERGY']) / main_categories_cpi_df.loc[i - 1, 'ALL ITEMS LESS FOOD AND ENERGY'] * 100
main_categories_cpi_df.set_index('MONTH', inplace=True)

twelve_month_cpi_df.reset_index(inplace=True)
for i in range(0, len(twelve_month_cpi_df)):
    twelve_month_cpi_df.loc[i, 'PERCENTAGE'] = main_categories_cpi_df.loc[twelve_month_cpi_df.loc[i, 'MONTH'], twelve_month_cpi_df.loc[i, 'PRODUCT'].upper() + ' PERCENTAGE']        
    
st.header('Consumer Price Index (CPI)')
col1, col2 = st.columns([3, 1])

chart1 = {
    "mark": "bar",
    "encoding": {
        "x": {"field": "MONTH"},
        "y": {"field": "VALUE", "type": "quantitative"},
        "xOffset": {"field": "PRODUCT"},
        "color": {"field": "PRODUCT"}
    }
}
col1.write('This chart below shows the CPI for selected catefories, not seasonally adjusted through 12 months in the US.')
col1.vega_lite_chart(twelve_month_cpi_df, chart1, use_container_width=True)

chart2 = {
    "mark": "bar",
    "encoding": {
        "x": {"field": "MONTH"},
        "y": {"field": "PERCENTAGE", "type": "quantitative"},
        "xOffset": {"field": "PRODUCT"},
        "color": {"field": "PRODUCT"}
    }
}
col1.write('This chart below shows the CPI percentage changes for selected catefories, not seasonally adjusted through 12 months in the US.')
col1.vega_lite_chart(twelve_month_cpi_df, chart2, use_container_width=True)

if (col2.checkbox('Show data', key='show_cpi_data_current_year')):
    col2.dataframe(main_categories_cpi_df)