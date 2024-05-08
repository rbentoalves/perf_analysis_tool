import os
from collections import defaultdict
from datetime import datetime
from glob import glob

import pandas as pd
import streamlit as st


def read_site_info():
    # Use a breakpoint in the code line below to debug your script.
    site_info_path = glob(os.path.join(os.getcwd(), 'General Info', 'Site Info.xlsx'))[0]
    site_info = pd.read_excel(site_info_path)

    return site_info

def kpis_analysis(site, analysis_start_date, analysis_end_date):

    irradiance_filtered, total_irradiance_period = get_irradiance_period()



    return

def get_irradiance_period(site, analysis_start_date, analysis_end_date):
    start_row = 5
    irradiance_path = glob(os.path.join(os.getcwd(), 'PerfData', site, '03. GHI-POA' , '*.xlsx'))[0]
    df_irradiance = pd.read_excel(irradiance_path, header = start_row,  index_col = 0)

    columns_poa = df_irradiance.columns[df_irradiance.columns.str.contains("POA")]

    granularity = (df_irradiance.index[1]-df_irradiance.index[0]).seconds/3600

    df_irradiance["Average POA"] = df_irradiance[columns_poa].mean(axis=1)
    irradiance_filtered = df_irradiance.loc[(df_irradiance["Average POA"] > 50)][analysis_start_date:analysis_end_date]
    total_irradiance_period = (irradiance_filtered["Average POA"].sum()/1000) * granularity

    return irradiance_filtered, total_irradiance_period

def get_site_level_data(site, analysis_start_date, analysis_end_date):


    return


def get_results_table(raw=[None, None, None, None, None],
                      corrected=[None, None, None, None, None]):
    data = {
        "Raw": raw,  # Placeholder for actual values
        "Corrected": corrected  # Placeholder for corrected values
    }
    index = ["Availability:", "PR(%):", "Energy Produced:", "Irradiance:", "Total Losses:"]
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

    profile_discount = ''

    SITE_INFO = read_site_info()
    ALL_SITE_LIST = SITE_INFO["Site"]
    SITE_DATA_AV = [os.path.basename(site) for site in glob(os.path.join(os.getcwd(), 'PerfData', '*'))]
    SITE_LIST = [site for site in ALL_SITE_LIST if site in SITE_DATA_AV]

    print(SITE_LIST)
    print(SITE_DATA_AV)
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
                results_table.dataframe(get_results_table(), use_container_width=True)


            if run_analysis_btn:
                if 'KPIs' in analysis:
                    kpis = kpis_analysis(site, analysis_start_date, analysis_end_date)




# See PyCharm help at https://www.jetbrains.com/help/pycharm/
