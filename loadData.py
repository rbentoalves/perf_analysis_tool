import os
from glob import glob
import pandas as pd
import datetime as dt
import re
pd.options.mode.chained_assignment = None  # default='warn'



def read_site_info():
    # Use a breakpoint in the code line below to debug your script.
    site_info_path = glob(os.path.join(os.getcwd(), 'General Info', 'Site Info.xlsx'))[0]
    site_info = pd.read_excel(site_info_path).set_index("Site", drop=True)



    return site_info

def read_general_info():
    # Use a breakpoint in the code line below to debug your script.
    general_info_path = glob(os.path.join(os.getcwd(), 'General Info', 'General Info.xlsx'))[0]
    all_general_info = pd.read_excel(general_info_path, sheet_name = None)
    budget_prod = all_general_info['Budget Export'].set_index("Site", drop=True)
    budget_irr = all_general_info['Budget Irradiance'].set_index("Site", drop=True)
    budget_pr = all_general_info['Budget PR'].set_index("Site", drop=True)
    component_data = all_general_info['Component Code']
    site_info = all_general_info["Site Info"]

    return all_general_info, budget_prod, budget_irr, budget_pr, component_data, site_info

def get_site_level_data(site, analysis_start_date, analysis_end_date, months):
    # Get start row of data, path to file and dataframe
    start_row = 6

    analysis_end_date_eff = analysis_end_date + dt.timedelta(days=1)


    for month in months:
        power_export_path = glob(os.path.join(os.getcwd(), 'PerfData', month, site, '02. Power', '*.xlsx'))[0]
        df_power_site_month = pd.read_excel(power_export_path, header=start_row, index_col=0)

        try:
            df_power_site = pd.concat([df_power_site, df_power_site_month])
        except NameError:
            df_power_site = df_power_site_month

    #Get relevant column and granularity of data
    column_site_power = df_power_site.columns[df_power_site.columns.str.contains('MLG_MLG')][0]
    df_power_site.rename(columns={column_site_power: "Site Power"}, inplace=True)
    #column_feeder_power = df_power_site.columns[df_power_site.columns.str.contains('MLG_MIL')]
    granularity = (df_power_site.index[1] - df_power_site.index[0]).seconds / 3600

    # Get dataset filtered by night values and timestamps
    power_period = df_power_site[analysis_start_date:analysis_end_date_eff]
    site_power_period = power_period[["Site Power"]]*1000
    site_power_filtered = site_power_period.loc[~(site_power_period["Site Power"] < 0)]

    # Calculate total energy exported in period
    total_energy_period = (site_power_period["Site Power"].sum()) * granularity

    return site_power_period, site_power_filtered, total_energy_period

def get_meter_data(site, analysis_start_ts, analysis_end_ts, months):
    # Get start row of data, path to file and dataframe

    for month in months:
        meter_export_path = glob(os.path.join(os.getcwd(), 'PerfData', month, site, '01. Energy', '*.xlsx'))[0]
        df_meter_site_month = pd.read_excel(meter_export_path,
                                            sheet_name='BASE_MWh_FORMULA', index_col=0)[["kWh rec int"]]
        try:
            df_meter_site_month = df_meter_site_month.drop(labels=0)
        except KeyError:
            pass


        try:
            df_meter_site = df_meter_site.drop(labels=df_meter_site_month.index)
            df_meter_site = pd.concat([df_meter_site, df_meter_site_month]).sort_index()
        except NameError:
            df_meter_site = df_meter_site_month

    #Change index to timestamps, rename column and get granularity of data
    df_meter_site.index = [pd.to_datetime(re.search(r'.*\s\d+\:\d+\:00', ts.replace(',', ' ')).group(),
                                          format = "%d/%m/%Y %H:%M:%S") for ts in df_meter_site.index]
    df_meter_site.rename(columns={'kWh rec int': "Meter Energy (MWh)"}, inplace=True)
    granularity = (df_meter_site.index[1] - df_meter_site.index[0]).seconds / 3600

    #Filter data for period in question
    meter_period = df_meter_site[analysis_start_ts:analysis_end_ts]
    meter_period["Meter Power (kW)"] = (meter_period["Meter Energy (MWh)"] * 1000) / granularity

    # Calculate total energy exported in period
    total_energy_meter_kwh = meter_period["Meter Energy (MWh)"].sum() * 1000

    return meter_period[["Meter Power (kW)"]], total_energy_meter_kwh


def get_inverter_level_data(site, analysis_start_ts, analysis_end_ts, months, irradiance_period, datapoint):
    start_row = 6

    for month in months:
        inverter_data_path = glob(os.path.join(os.getcwd(), 'PerfData', month, site, '04. Inverter Power', datapoint,
                                               '*.xlsx'))  # replace general_folder with os.getcwd()
        dfs_list = [pd.read_excel(path, header=start_row, index_col=0)[analysis_start_ts:analysis_end_ts] for path
                    in inverter_data_path]
        dfs_list = [df.rename_axis('Timestamp (15m)') for df in dfs_list]
        all_data_df_month = pd.concat(dfs_list, axis=1)

        try:
            all_data_df_invs = pd.concat([all_data_df_invs, all_data_df_month])
        except NameError:
            all_data_df_invs = all_data_df_month

    all_data_df = pd.concat([irradiance_period[["Avg Irradiance POA", "Avg Irradiance GHI"]], all_data_df_invs], axis=1)
    all_data_df = all_data_df.loc[(all_data_df["Avg Irradiance POA"] > 20)]

    return all_data_df

def get_irradiance_period(site, analysis_start_ts, analysis_end_ts, months, round_to: int = 15):
    # Get start row of data, path to file and dataframe
    start_row = 5
    #irradiance_path = glob(os.path.join(os.getcwd(), 'PerfData', site, '03. GHI-POA' , '*.xlsx'))[0]
    for month in months:
        #print(month)
        irradiance_path = glob(os.path.join(os.getcwd(), 'PerfData', month, site, '03. GHI-POA', '*.xlsx'))[0]
        df_irradiance_list = pd.read_excel(irradiance_path, header=start_row, sheet_name=None, index_col=0)
        df_irradiance_month = pd.concat(list(df_irradiance_list.values()), axis=1)
        df_irradiance_month = df_irradiance_month.rename_axis('Timestamp (1m)')
        df_irradiance_month = df_irradiance_month.loc[:, ~df_irradiance_month.columns.str.contains('^Unnamed')]


        try:
            df_irradiance = pd.concat([df_irradiance, df_irradiance_month])
        except NameError:
            df_irradiance = df_irradiance_month


    # Get relevant column and granularity of data
    columns_poa = df_irradiance.columns[df_irradiance.columns.str.contains("POA")]
    columns_ghi = df_irradiance.columns[df_irradiance.columns.str.contains("GHI")]

    granularity = (df_irradiance.index[1] - df_irradiance.index[0]).seconds / 3600

    # Average data, filter for threshold and timestamps
    df_irradiance["Avg Irradiance POA"] = df_irradiance[columns_poa].mean(axis=1)
    df_irradiance["Avg Irradiance GHI"] = df_irradiance[columns_ghi].mean(axis=1)

    raw_irradiance_period = df_irradiance[analysis_start_ts:analysis_end_ts]
    irradiance_filtered = df_irradiance.loc[(df_irradiance["Avg Irradiance POA"] > 0)][
                          analysis_start_ts:analysis_end_ts]

    # Get 15min dataset
    column_name = "Timestamp (" + str(round_to) + "m)"
    round_to_str = str(round_to) + "min"

    raw_irradiance_period[column_name] = list(
        pd.Series(raw_irradiance_period.index).dt.round(round_to_str, 'shift_forward'))
    irradiance_period_rounded = raw_irradiance_period.groupby([column_name]).mean()

    # Calculate total irradiance in period
    total_irradiance_period = (irradiance_filtered["Avg Irradiance POA"].sum() / 1000) * granularity

    return raw_irradiance_period, irradiance_period_rounded, irradiance_filtered, total_irradiance_period

def get_incident_timestamps(df_relevant_data, prev_ts, next_ts, df_timedelta):
    for index_i in range(len(df_relevant_data)):
        timestamp = df_relevant_data.index[index_i]
        delta_to_prev = df_relevant_data.iloc[index_i]["Timedelta to previous"]
        delta_to_next = df_relevant_data.iloc[index_i]["Timedelta to next"]

        if delta_to_prev != df_timedelta:
            df_relevant_data.loc[timestamp, "Start/End Event"] = "Start"
            df_relevant_data.loc[timestamp, "Incident TS"] = timestamp

            # If next timestamp is diff from +delta then get close timestamp
            try:
                next_timestamp = df_relevant_data.index[index_i + 1]
                if (timestamp + df_timedelta) != next_timestamp:
                    df_relevant_data.loc[timestamp, "End Incident TS"] = next_timestamp

            except IndexError:
                df_relevant_data.loc[timestamp, "End Incident TS"] = (timestamp + df_timedelta)


        elif delta_to_prev != df_timedelta and delta_to_next != dt.timedelta(minutes=0):
            df_relevant_data.loc[timestamp, "Start/End Event"] = "End"
            df_relevant_data.loc[timestamp, "End Incident TS"] = timestamp

        elif delta_to_next != df_timedelta:
            df_relevant_data.loc[timestamp, "Start/End Event"] = "End"
            df_relevant_data.loc[timestamp, "End Incident TS"] = timestamp + df_timedelta

    events_start = list(df_relevant_data["Incident TS"].dropna())
    events_end = list(df_relevant_data["End Incident TS"].dropna())

    if len(events_end) == 0:
        events_end = [timestamp + df_timedelta for timestamp in events_start]

    elif len(events_start) > len(events_end):
        to_insert = events_start[-1] + df_timedelta
        events_end.insert(len(events_end), events_start[-1] + df_timedelta)

    return df_relevant_data, events_start, events_end

def create_component_incidents_dataframe(component_capacity, component, site, df_relevant_data, night_error_component,
                                         df_timedelta):
    len_index = len(df_relevant_data.index)
    component_column = df_relevant_data.columns[df_relevant_data.columns.str.contains(component)][0]

    if len_index == 1:
        events_start = [df_relevant_data.index[0]]
        events_end = [df_relevant_data.index[0] + df_timedelta]
    else:

        prev_ts = list(df_relevant_data.index[:len_index - 1].insert(0, df_relevant_data.index[0]))
        next_ts = list(df_relevant_data.index[1:].insert(len_index - 1, df_relevant_data.index[len_index - 1]))

        df_relevant_data["Timedelta to previous"] = pd.to_datetime(df_relevant_data.index) - pd.to_datetime(prev_ts)
        df_relevant_data["Timedelta to next"] = pd.to_datetime(next_ts) - pd.to_datetime(df_relevant_data.index)

        df_relevant_data["Start/End Event"] = ["No"] * len_index
        df_relevant_data["Incident TS"] = [pd.NA] * len_index
        df_relevant_data["End Incident TS"] = [pd.NA] * len_index

        df_relevant_data, events_start, events_end = get_incident_timestamps(df_relevant_data, prev_ts, next_ts,
                                                                             df_timedelta)

    status_data = []
    for i in range(len(events_start)):
        data_event = df_relevant_data.loc[events_start[i]:events_end[i], :]
        data_event_0 = data_event.loc[data_event[component_column] == 0]

        if data_event_0.empty:
            status_data.append("No Comms")
        else:
            status_data.append("Not Producing")

    df_dict = {"Site Name": [site] * len(events_start),
               "Component": [component] * len(events_start),
               "Capacity related component": [component_capacity] * len(events_start),
               "Status": status_data,
               "Event Start Time": events_start,
               "Event End Time": events_end,
               "Duration (h)": [pd.NA] * len(events_start),
               "Active hours (h)": [pd.NA] * len(events_start),
               "Irradiation period": [pd.NA] * len(events_start),
               "Energy lost (kWh)": [pd.NA] * len(events_start),
               "Weighted downtime %": [pd.NA] * len(events_start),
               "Approved": [""] * len(events_end)}

    df = pd.DataFrame.from_dict(df_dict)

    return df, df_relevant_data


def get_incidents_df(all_data_df, component_data, site):
    df_timedelta = all_data_df.index[1] - all_data_df.index[0]
    for column in all_data_df.columns:
        if "Irradiance" not in column:
            inv_data = all_data_df[[column]]
            np_data = inv_data.loc[(inv_data[column] == 0) | (pd.isna(inv_data[column]))]
            if not np_data.empty:
                component = re.search(r'STS.*IN\d\d', np_data.columns[0]).group()
                print("Creating incidents for " + component)
                night_error_component = 0
                try:
                    component_capacity = \
                    component_data.loc[(component_data["Site"] == site) & (component_data["Component"] == component)][
                        "Nominal Power DC"].values[0]

                    comp_incident_df, df_relevant_data = create_component_incidents_dataframe(component_capacity,
                                                                                              component, site, np_data,
                                                                                              night_error_component,
                                                                                              df_timedelta)



                    try:
                        df_all_incidents = pd.concat([df_all_incidents, comp_incident_df])
                    except NameError:
                        df_all_incidents = comp_incident_df


                except IndexError:
                    print(component + " not found on component list")

    df_all_incidents.sort_values(by=["Status", "Event Start Time", 'Component'], ascending=[False, True, True],
                                 inplace=True)
    df_all_incidents.reset_index(inplace=True, drop=True)

    return df_all_incidents

def read_Event_Tracker(site, approved: bool = False):
    try:
        event_tracker_path = glob(os.path.join(os.getcwd(), 'Results', site, 'Event Tracker ' + site + '.xlsx'))[0]
        print(event_tracker_path)
        if approved:
            df_incidents_ET = pd.read_excel(event_tracker_path, sheet_name='Approved Incidents')
        else:
            df_incidents_ET = pd.read_excel(event_tracker_path, sheet_name='Incidents')

    except IndexError:
        df_incidents_ET = pd.DataFrame()
        curtailment_df_ET = pd.DataFrame()

        return df_incidents_ET, curtailment_df_ET

    try:
        curtailment_df_ET = pd.read_excel(event_tracker_path, sheet_name='Curtailment incidents')

    except ValueError:
        curtailment_df_ET = pd.DataFrame()

    return df_incidents_ET, curtailment_df_ET


def get_setpoint_data(site, months,SITE_INFO):
    for month in months:
        setpoint_path = glob(os.path.join(os.getcwd(), 'PerfData', month, site, '06. PPC Setpoint', '*.csv'))[0]
        print(setpoint_path)
        df_setpoint_month = pd.read_csv(setpoint_path,sep=';', encoding='latin', on_bad_lines='skip')

        try:
            df_setpoint = pd.concat([df_setpoint, df_setpoint_month])
        except NameError:
            df_setpoint = df_setpoint_month

    #Rename Columns

    df_setpoint.rename(columns={'Data e hora sistema': 'Timestamp',
                                'Hierarquia': 'Level',
                                'Estado': "Setpoint value",
                                'Descrição': 'Setpoint active'}, inplace=True)



    #SELECT RELEVANT DATA
    df_setpoint = df_setpoint[['Timestamp','Setpoint value', 'Setpoint active', 'Level']]
    df_setpoint = df_setpoint.loc[df_setpoint["Level"].str.contains('PPC_MLG - MLG')]


    #TRANSFORM DATA AND ORDER TABLE
    df_setpoint["Timestamp"] = [pd.to_datetime(re.search(r'.*\s\d+\:\d+\:\d+', ts.replace(',', ' ')).group(),
                                          format = "%d/%m/%Y %H:%M:%S") for ts in df_setpoint["Timestamp"]]

    df_setpoint["Setpoint value"] = [round(float(value.replace(',','.')) * 1000) for value in df_setpoint["Setpoint value"]]

    df_setpoint = df_setpoint.sort_values(by=["Timestamp"],ascending=True).reset_index(drop = True)
    print(df_setpoint)

    #GET EVENTS TIMESTAMPS
    nominal_power_dc = float(SITE_INFO.loc["Milagres", 'Nominal Power DC'])
    max_export_setpoint = float(SITE_INFO.loc["Milagres", 'Maximum Export Capacity'])
    print(max_export_setpoint)

    events_active_index = list(df_setpoint.loc[df_setpoint["Setpoint value"] < max_export_setpoint].index)
    events_end_index = list(df_setpoint.loc[df_setpoint["Setpoint value"] >= max_export_setpoint].index)
    events_start_index = [i + 1 for i in events_end_index if i + 1 in events_active_index]

    min_index_start = min(events_start_index)
    max_index_end = max(events_end_index)

    events_start_index = [i for i in events_start_index if i < max_index_end]
    events_end_index = [i for i in events_end_index if i > min_index_start and i+1 in events_active_index]

    if max_index_end not in events_end_index:
        events_end_index.append(max_index_end)

    events_start_df = df_setpoint.loc[events_start_index,:]
    events_end_df = df_setpoint.loc[events_end_index, :]

    df_dict = {"Site Name": [site] * len(events_start_index),
               "Component": ["Milagres"] * len(events_start_index),
               "Capacity related component": [nominal_power_dc] * len(events_start_index),
               "Status": ["Curtailment"] * len(events_start_index),
               "Event Start Time": list(events_start_df["Timestamp"]),
               "Event End Time": list(events_end_df["Timestamp"]),
               "Duration (h)": [pd.NA] * len(events_start_index),
               "Active hours (h)": [pd.NA] * len(events_start_index),
               "Irradiation period": [pd.NA] * len(events_start_index),
               "Energy lost (kWh)": [pd.NA] * len(events_start_index),
               "Weighted downtime %": [pd.NA] * len(events_start_index),
               "Approved": ["x"] * len(events_start_index)}

    curtailment_df = pd.DataFrame.from_dict(df_dict)


    return curtailment_df