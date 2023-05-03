import streamlit as st
import pandas as pd

from functions import init_connection

st.set_page_config(
     page_title="U.S. Bureau of labor statistics",
     page_icon="🧊",
     layout="wide",
     initial_sidebar_state="expanded"
)

st.title('🧊 Bureau of Labor Statistics: CPI, JOLTS, Employment and Unemployment')
st.subheader('The Bureau of Labor Statistics (BLS) publishes the Consumer Price Index (CPI), Average Prices (AP), Job Openings and Labor Turnover Survey (JOLTS), State and Metro Area Employment , Hours, & Earnings (SAE), Local Area Unemployment Statistics (LAUS) on a monthly basis.')

conn = init_connection()
cur = conn.cursor()

# Load data table
@st.cache_resource
def load_us_annual_cpi_data():    
    cur.execute("SELECT VARIABLE, VARIABLE_NAME, VALUE, DATE FROM BLS_PRICE_TIMESERIES "
        + "WHERE GEO_ID = 'country/USA' AND VARIABLE IN ('CPI:_Food,_Not_seasonally_adjusted,_Annual', "
        + "'CPI:_All_items,_Not_seasonally_adjusted,_Annual', "
        + "'CPI:_Energy,_Not_seasonally_adjusted,_Annual', "
        + "'CPI:_All_items_less_food_and_energy,_Not_seasonally_adjusted,_Annual')")
    return cur.fetch_pandas_all()

# @st.cache_resource
# def load_price_attributes_data():
#     cur.execute("SELECT * FROM BLS_PRICE_ATTRIBUTES WHERE REPORT = 'Consumer Price Index'")
#     return cur.fetch_pandas_all()

@st.cache_resource
def load_us_employment_data():
    cur.execute("SELECT ts.variable, VALUE, DATE, MEASURE, INDUSTRY "
        + "FROM bls_employment_timeseries as ts "
        + "JOIN cybersyn.bls_employment_attributes AS att ON (ts.variable = att.variable) "
        + "WHERE geo_id = 'country/USA' AND att.unit = 'Level' AND REPORT = 'JOLTS' AND FREQUENCY = 'Annual'")
    return cur.fetch_pandas_all()

us_anual_cpi_df = load_us_annual_cpi_data()
us_anual_cpi_df['YEAR'] = pd.DatetimeIndex(us_anual_cpi_df['DATE']).year
us_anual_cpi_df= us_anual_cpi_df.sort_values(by=['YEAR'])

def build_category_cpi_df(key, variable):
    df = us_anual_cpi_df[us_anual_cpi_df['VARIABLE'] == variable];
    df[key] = df['VALUE']
    df = df.filter(items=[key, 'YEAR'])
    df.set_index('YEAR', inplace=True)

    return df

food_df = build_category_cpi_df('FOOD', 'CPI:_Food,_Not_seasonally_adjusted,_Annual')
all_items_df = build_category_cpi_df('ALL ITEMS', 'CPI:_All_items,_Not_seasonally_adjusted,_Annual')
energy_df = build_category_cpi_df('ENERGY', 'CPI:_Energy,_Not_seasonally_adjusted,_Annual')
all_items_less_food_and_energy_df = build_category_cpi_df('ALL ITEMS LESS FOOD AND ENERGY', 'CPI:_All_items_less_food_and_energy,_Not_seasonally_adjusted,_Annual')

main_categories_cpi_df = pd.merge(left=all_items_df, right=food_df, how='outer', left_index=True, right_index=True)
main_categories_cpi_df = main_categories_cpi_df.merge(energy_df, how='outer', left_index=True, right_index=True)
main_categories_cpi_df = main_categories_cpi_df.merge(all_items_less_food_and_energy_df, how='outer', left_on='YEAR', right_on='YEAR')

with st.container():
    st.header('Consumer Price Index (CPI)')
    st.text('CPI is a measure of the average change over time in the prices paid by urban consumers for a market basket of consumer goods and services.')
    col1, col2 = st.columns([3, 1])

    end_year = int(main_categories_cpi_df.index.max())
    start_year = end_year - 20
    col1.subheader('Years')
    selected_range_start, selected_range_end = col1.select_slider('Select a range of years to see how CPI has changed.', options=main_categories_cpi_df.index, value=(start_year, end_year))
    main_categories_cpi_df = main_categories_cpi_df[main_categories_cpi_df.index >= selected_range_start]
    main_categories_cpi_df = main_categories_cpi_df[main_categories_cpi_df.index <= selected_range_end]
    main_categories_cpi_df.index = main_categories_cpi_df.index.astype(str)
    col1.line_chart(main_categories_cpi_df)


    if (col2.checkbox('Show data', key='show_cpi_data')):
        col2.dataframe(main_categories_cpi_df)

us_employment_df = load_us_employment_data()
us_employment_df['YEAR'] = pd.DatetimeIndex(us_employment_df['DATE']).year

def build_employment_dataframe(key, measure):
    df = us_employment_df[us_employment_df['MEASURE'] == measure]
    df = df.groupby('YEAR', as_index = False)['VALUE'].sum()
    df[key] = df['VALUE']
    df = df.filter(items=['YEAR', key])
    df.set_index('YEAR', inplace=True)

    return df


layoffs_df = build_employment_dataframe('LAYOFFS', 'Layoffs and discharges')
hires_df = build_employment_dataframe('HIRES', 'Hires')
job_openings_df = build_employment_dataframe('JOB OPENINGS', 'Job openings')
other_separations_df = build_employment_dataframe('OTHER SEPARATIONS', 'Other separations')
quits_df = build_employment_dataframe('QUITS', 'Quits')

employment_df = pd.merge(left=job_openings_df, right=hires_df, how='outer', left_index=True, right_index=True)
employment_df = employment_df.merge(quits_df, how='outer', left_index=True, right_index=True)
employment_df = employment_df.merge(layoffs_df, how='outer', left_index=True, right_index=True)
employment_df = employment_df.merge(other_separations_df, how='outer', left_index=True, right_index=True)

with st.container():
    st.header('Job Openings and Labor Turnover Survey (JOLTS)')
    st.text('JOLTS provides data on job openings, hires, and separations at the national and state level. The job openings rate can help measure the tightness of job markets.')
    st.markdown('* Job Openings: All positions that are open (not filled) on the last business day of the month.')
    st.markdown('* Hires: All additions to the payroll during the month.')
    st.markdown('* Quits: Employees who left voluntarily. Exception: retirements or transfers to other locations are reported with Other Separations.')
    st.markdown('* Layoffs & Discharges: Involuntary separations initiated by the employer.')
    st.markdown('* Other Separations: Retirements, transfers to other locations; deaths; or separations due to employee disability.')

    col1, col2 = st.columns([3, 1])

    col1.line_chart(employment_df)
    if (col2.checkbox('Show data', key='show_jolts_data')):
        col2.dataframe(employment_df)
    