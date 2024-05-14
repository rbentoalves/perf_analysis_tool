import os
from collections import defaultdict
from datetime import datetime
from glob import glob

import pandas as pd
import streamlit as st


def read_site_info():
    # Use a breakpoint in the code line below to debug your script.
    site_info_path = glob(os.path.join(os.getcwd(), 'General Info', 'Site Info.xlsx'))[0]
    site_info = pd.read_excel(site_info_path).set_index("Site", drop=True)
    print(site_info)


    return site_info

def read_general_info():
    # Use a breakpoint in the code line below to debug your script.
    general_info_path = glob(os.path.join(os.getcwd(), 'General Info', 'General Info.xlsx'))[0]
    all_general_info = pd.read_excel(general_info_path, sheet_name = None)
    budget_prod = all_general_info['Budget Export'].set_index("Site", drop=True)
    budget_irr = all_general_info['Budget Irradiance'].set_index("Site", drop=True)
    budget_pr = all_general_info['Budget PR'].set_index("Site", drop=True)

    return budget_prod, budget_irr, budget_pr



def kpis_analysis(site, analysis_start_date, analysis_end_date, site_info):
    budget_prod, budget_irr, budget_pr = read_general_info()
    irradiance_filtered, total_irradiance_period = get_irradiance_period(site, analysis_start_date, analysis_end_date)
    site_power_filtered, total_energy_period = get_site_level_data(site, analysis_start_date, analysis_end_date)
    budget_values_date = datetime.combine(analysis_start_date, datetime.min.time())

    # Calculate PR%
    pr_period = (total_energy_period*1000) / (total_irradiance_period * site_info.loc[site,'Nominal Power DC'])
    print('Site PR%: ' , format(pr_period, ".2%"))

    '''full_results = pd.DataFrame(data=form.results.cashflows,
                                columns=['Date', 'Volume', 'Discount', 'Certificates', 'Value'], )'''

    #index = ["Availability:", "PR(%):", "Energy Produced:", "Irradiance:", "Total Losses:"]

    actual = [None, None, None, None, None]
    budget = ['100.00 %', None, None, None,'0']

    actual[1] = format(pr_period, ".2%")
    actual[2] = format(total_energy_period, ".2f")
    actual[3] = format(total_irradiance_period, ".2f")

    budget[1] = format(budget_pr.loc[site, budget_values_date], ".2%")
    budget[2] = format(budget_prod.loc[site, budget_values_date], ".2f")
    budget[3] = format(budget_irr.loc[site, budget_values_date], ".2f")

    return get_results_table(site, actual, budget)

def get_irradiance_period(site, analysis_start_date, analysis_end_date):
    # Get start row of data, path to file and dataframe
    start_row = 5
    irradiance_path = glob(os.path.join(os.getcwd(), 'PerfData', site, '03. GHI-POA' , '*.xlsx'))[0]
    df_irradiance = pd.read_excel(irradiance_path, header = start_row,  index_col = 0)

    # Get relevant column and granularity of data
    columns_poa = df_irradiance.columns[df_irradiance.columns.str.contains("POA")]
    granularity = (df_irradiance.index[1]-df_irradiance.index[0]).seconds/3600

    # Average data, filter for threshold and timestamps
    df_irradiance["Average POA"] = df_irradiance[columns_poa].mean(axis=1)
    irradiance_filtered = df_irradiance.loc[(df_irradiance["Average POA"] > 50)][analysis_start_date:analysis_end_date]

    # Calculate total irradiance in period
    total_irradiance_period = (irradiance_filtered["Average POA"].sum()/1000) * granularity

    return irradiance_filtered, total_irradiance_period

def get_site_level_data(site, analysis_start_date, analysis_end_date):
    # Get start row of data, path to file and dataframe
    start_row = 6
    power_export_path = glob(os.path.join(os.getcwd(), 'PerfData', site, '02. Power', '*.xlsx'))[0]
    df_power_site = pd.read_excel(power_export_path, header=start_row, index_col=0)

    #Get relevant column and granularity of data
    column_power = df_power_site.columns[df_power_site.columns.str.contains('MLG_MLG')][0]
    granularity = (df_power_site.index[1] - df_power_site.index[0]).seconds / 3600

    # Get dataset filtered by night values and timestamps
    print(column_power)
    site_power_filtered = df_power_site.loc[~(df_power_site[column_power] < 0)][analysis_start_date:analysis_end_date]

    # Calculate total energy exported in period
    total_energy_period = (df_power_site[column_power].sum()) * granularity

    return site_power_filtered, total_energy_period


def get_results_table(site = False,
                      actual=[None, None, None, None, None],
                      budget=[None, None, None, None, None]):

    data = {
        "Actual": actual,  # Placeholder for actual values
        "Budget": budget  # Placeholder for corrected values
    }
    index = ["Availability:", "PR(%):", "Energy Produced (kWh):", "Irradiation:", "Total Losses (kWh):"]
    # Create the DataFrame
    return pd.DataFrame(data, index=index)



def get_site_list(all_site_info):
    # Use a breakpoint in the code line below to debug your script.
    site_list = all_site_info["Site Name"]

    return site_info, site_list

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    st.set_page_config(page_title="Performance Analysis tool",
                       page_icon="☀️",
                       layout="wide")

    profile_mainkpis = ''

    SITE_INFO = read_site_info()
    ALL_SITE_LIST = SITE_INFO.index
    SITE_DATA_AV = [os.path.basename(site) for site in glob(os.path.join(os.getcwd(), 'PerfData', '*'))]
    SITE_LIST = [site for site in ALL_SITE_LIST if site in SITE_DATA_AV]

    #HYPO_ASSETS = fetch_hypo_assets()

    st.title('☀️ Performance Analysis tool')
    main_kpis_tab, inverter_dd_tab, cb_dd_tab, results_tab, debug_tab = st.tabs(['Main KPIs', 'Inverter DD', 'DC Box DD', 'Results', 'Profiler'])


    with (main_kpis_tab):
        with st.container():
            r1_1, r1_2 = st.columns(2)
            with r1_1:
                with st.expander('General Inputs', expanded=True):
                    g1_1, g1_2 = st.columns(2)
                    with g1_1:
                        analysis_start_date = st.date_input('Start date')
                        analysis_end_date = st.date_input('End date', min_value=analysis_start_date)

                        site = st.selectbox('Site Selection', SITE_LIST)

                    with g1_2:
                        analysis = st.multiselect('Analysis to conduct', ['KPIs', 'Inverter outages', 'DC Box Relative Performance'])
                        def disable(b):
                            st.session_state["analysis_run_disabled"] = b

                        run_analysis_btn = st.button('Run Analysis', use_container_width=True, on_click=disable, args=(True,),
                                                     disabled=st.session_state.get("analysis_run_disabled", False))

                        if st.button("Reset All?", on_click=disable, args=(False,), use_container_width=True):
                            st.rerun()

            with r1_2:
                results_table = st.empty()
                results_table.dataframe(get_results_table(site), use_container_width=True)

    with (debug_tab):
        debug_text = st.empty()
        debug_text.code(profile_mainkpis)


    if run_analysis_btn:
        if 'KPIs' in analysis:
            from pyinstrument import Profiler

            profiler = Profiler()
            profiler.start()

            result = kpis_analysis(site, analysis_start_date, analysis_end_date, SITE_INFO)

            profiler.stop()
            profile_mainkpis = profiler.output_text()
            debug_text.code(profile_mainkpis)


            st.snow()
            results_table.dataframe(result, use_container_width=True)








# See PyCharm help at https://www.jetbrains.com/help/pycharm/
