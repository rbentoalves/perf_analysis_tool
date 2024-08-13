import os
from datetime import datetime
from glob import glob
import pandas as pd
import streamlit as st
import altair as alt
import loadData
import calcData

def populate_results_df(site, budget_values_date,
                        pr_period, total_energy_period, total_irradiance_period,
                        budget_pr, budget_prod, budget_irr):

    actual = [None, None, None, None, None]
    budget = ['100.00 %', None, None, None, '0']

    actual[1] = format(pr_period, ".2%")
    actual[2] = format(total_energy_period, ".2f")
    actual[3] = format(total_irradiance_period, ".2f")

    budget[1] = format(budget_pr.loc[site, budget_values_date], ".2%")
    budget[2] = format(budget_prod.loc[site, budget_values_date], ".2f")
    budget[3] = format(budget_irr.loc[site, budget_values_date], ".2f")


    return actual, budget


def kpis_analysis(site, analysis_start_date, analysis_end_date, months, site_info):
    print("Reading Irradiance")
    raw_irradiance_period, irradiance_period_15m, irradiance_filtered, total_irradiance_period = loadData.get_irradiance_period(site, analysis_start_date, analysis_end_date, months)
    print("Reading site level power")
    site_power_period, site_power_filtered, total_energy_period = loadData.get_site_level_data(site, analysis_start_date, analysis_end_date, months)
    print("Reading Budget data")
    #add other months, right now it only looks at the first
    budget_values_date = datetime.combine(analysis_start_date, datetime.min.time()).replace(day=1)

    # Calculate PR%
    pr_period = (total_energy_period) / (total_irradiance_period * site_info.loc[site,'Nominal Power DC'])
    print('Site PR%: ' , format(pr_period, ".2%"))

    #Get Availability results

    all_data_df = loadData.get_inverter_level_data(site, analysis_start_date, analysis_end_date, months, raw_irradiance_period, "AC Power")
    df_timedelta = all_data_df.index[1] - all_data_df.index[0]

    #df_all_incidents = loadData.get_incidents_df(all_data_df, component_data, site)
    #df_all_incidents = calcData.calculate_incident_losses(df_all_incidents, all_data_df, site, all_general_info,
                                                          #budget_pr, df_timedelta)

    #site_availability, inverter_availability = calcData.calculate_availability(df_all_incidents, all_data_df, df_timedelta)


    #Populate results table
    actual, budget = populate_results_df(site, budget_values_date, pr_period,
                                         total_energy_period, total_irradiance_period,
                                         budget_pr, budget_prod, budget_irr)

    #Get chart data
    #print(site_power_period)
    raw_data = site_power_period.join(raw_irradiance_period[["Avg Irradiance POA", "Avg Irradiance GHI"]])
    #print(raw_data)


    return get_results_table(site, actual, budget), get_chart_results(site, raw_data), raw_irradiance_period

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


def get_chart_results(site = False, data = 0, index = 0):
    if site:
        data.index.names = ['Timestamp']
        data = data.reset_index()


        irradiance_poa = alt.Chart(data).mark_line().encode(
            x='Timestamp', y='Avg Irradiance POA', color=alt.value("#1f77b4"))

        #irradiance_ghi = alt.Chart(data).mark_area(opacity=0.9).encode(
         #   x='Timestamp', y='Avg Irradiance GHI')

        site_power = alt.Chart(data).mark_line().encode(
            x='Timestamp', y='Site Power', color=alt.value("#ff7f0e"))

        chart_data = alt.layer(irradiance_poa, site_power).resolve_scale(
            y='independent')



        #pd.DataFrame(data) #, index=index)
    else:
        chart_data = pd.DataFrame({'No data' : [0]})

    return chart_data

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    st.set_page_config(page_title="Performance Analysis tool",
                       page_icon="☀️",
                       layout="wide")

    profile_mainkpis = ''

    SITE_INFO = loadData.read_site_info()
    ALL_SITE_LIST = SITE_INFO.index
    SITE_LIST = set([os.path.basename(site) for site in glob(os.path.join(os.getcwd(), 'PerfData', '*', '*'))])
    #SITE_LIST = [site for site in ALL_SITE_LIST if site in SITE_DATA_AV]

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

        with st.container():
            results_chart = st.empty()
            #results_chart.scatter_chart(get_chart_results(), use_container_width=True)

    with (debug_tab):
        debug_text = st.empty()
        debug_text.code(profile_mainkpis)


    if run_analysis_btn:
        from pyinstrument import Profiler

        profiler = Profiler()
        profiler.start()

        print(SITE_INFO)

        all_general_info, budget_prod, budget_irr, budget_pr, component_data, site_info = loadData.read_general_info()

        months = list(pd.date_range(analysis_start_date.replace(day=1),
                                    analysis_end_date.replace(day=1, month=analysis_end_date.month + 1),
                                    freq='M'))
        months = [
            str(timestamp.month) + "." + str(timestamp.year) if timestamp.month > 10 else '0' + str(
                timestamp.month) + "." + str(timestamp.year) for timestamp in months]

        print(analysis_start_date)
        print(analysis_end_date)
        print(months)

        if 'KPIs' in analysis:

            result, chart, irradiance_data = kpis_analysis(site, analysis_start_date, analysis_end_date, months, SITE_INFO)


            results_table.dataframe(result, use_container_width=True)
            #results_chart.line_chart(chart, use_container_width=True)
            results_chart.altair_chart(chart, use_container_width=True)

        if "Inverter outages" in analysis:
            all_data_df = loadData.get_inverter_level_data(site, analysis_start_date, analysis_end_date, months, irradiance_data, "AC Power")
            df_timedelta = all_data_df.index[1] - all_data_df.index[0]

            df_all_incidents = loadData.get_incidents_df(all_data_df, component_data, site)
            df_all_incidents = calcData.calculate_incident_losses(df_all_incidents, all_data_df, site, all_general_info, budget_pr, df_timedelta)
            pass






        profiler.stop()
        profile_mainkpis = profiler.output_text()
        debug_text.code(profile_mainkpis)

        st.snow()









# See PyCharm help at https://www.jetbrains.com/help/pycharm/
