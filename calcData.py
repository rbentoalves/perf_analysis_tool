import re
import datetime as dt

import pandas as pd


def calculate_incident_losses(df_all_incidents, all_data_df, site, all_general_info, budget_pr, df_timedelta):
    site_info = all_general_info["Site Info"]
    site_capacity = site_info.loc[site_info["Site"] == site]["Nominal Power DC"].values[0]
    site_active_hours = len(all_data_df[["Avg Irradiance POA"]]) * (df_timedelta.seconds / 3600)

    irradiance_data = all_data_df[["Avg Irradiance POA"]]
    irradiance_data["Budget PR"] = [budget_pr.loc[site, timestamp.replace(day=1, hour=0, minute=0, second=0)] for
                                    timestamp in irradiance_data.index]

    for index, row in df_all_incidents.iterrows():
        incident_irradiance = irradiance_data.loc[row["Event Start Time"]:row["Event End Time"], :]
        incident_irradiance_total = \
        (incident_irradiance[["Avg Irradiance POA"]].sum() * (df_timedelta.seconds / 3600)).values[0]

        duration = (row['Event End Time'] - row["Event Start Time"]).seconds / 3600
        active_hours = (len(incident_irradiance) - 1) * (df_timedelta.seconds / 3600)
        if active_hours < 0:
            active_hours = 0

        energy_lost = (
                (incident_irradiance["Avg Irradiance POA"] * incident_irradiance["Budget PR"] / 1000).sum() * (
                    df_timedelta.seconds / 3600) * row["Capacity related component"])

        df_all_incidents.at[index, "Duration (h)"] = duration
        df_all_incidents.at[index, "Active hours (h)"] = active_hours
        df_all_incidents.at[index, "Irradiation period"] = incident_irradiance_total
        df_all_incidents.at[index, "Energy lost (kWh)"] = energy_lost
        df_all_incidents.at[index, "Weighted downtime %"] = active_hours * (
                row["Capacity related component"] / site_capacity) / site_active_hours

    return df_all_incidents

def calculate_availability(df_all_incidents, all_data_df, all_general_info, df_timedelta):
    component_data = all_general_info['Component Code']
    site_active_hours = len(all_data_df[["Avg Irradiance POA"]]) * (df_timedelta.seconds / 3600)
    site_availability = 1 - df_all_incidents["Weighted downtime %"].sum()
    inverter_list = list(component_data.loc[component_data["Component Type"] == "Inverter"]["Component"])
    inverter_availability = {}

    for component in inverter_list:
        comp_incident = df_all_incidents.loc[df_all_incidents["Component"] == component]
        component_availability = 1 - comp_incident["Weighted downtime %"].sum()

        inverter_availability[component] = component_availability

    return site_availability, inverter_availability


def calculate_curtailment_losses(curtailment_df, site_data, site, all_general_info):
    df_timedelta = site_data.index[1] - site_data.index[0]
    site_info = all_general_info["Site Info"]
    site_capacity = site_info.loc[site_info["Site"] == site]["Nominal Power DC"].values[0]
    site_active_hours = len(site_data[["Avg Irradiance POA"]]) * (df_timedelta.seconds / 3600)


    for index, row in curtailment_df.iterrows():
        incident_data = site_data.loc[row["Event Start Time"]:row["Event End Time"], :]
        incident_irradiance_total = (incident_data[["Avg Irradiance POA"]].sum()
                                     * (df_timedelta.seconds / 3600)).values[0]

        duration = (row['Event End Time'] - row["Event Start Time"]).seconds / 3600
        active_hours = ((len(incident_data.loc[incident_data["Meter Power (kW)"] <= 0]) - 1)
                        * (df_timedelta.seconds / 3600))
        if active_hours < 0:
            active_hours = 0
        energy_lost = ((incident_data["Expected Power"].sum() - incident_data["Meter Power (kW)"].sum()) *
                       (df_timedelta.seconds / 3600))

        curtailment_df.at[index, "Duration (h)"] = duration
        curtailment_df.at[index, "Active hours (h)"] = active_hours
        curtailment_df.at[index, "Irradiation period"] = incident_irradiance_total
        curtailment_df.at[index, "Energy lost (kWh)"] = energy_lost
        curtailment_df.at[index, "Weighted downtime %"] = active_hours * (
                row["Capacity related component"] / site_capacity) / site_active_hours

    total_curtailment_loss = curtailment_df["Energy lost (kWh)"].sum()
    exported_energy = site_data["Meter Power (kW)"].sum() * (df_timedelta.seconds / 3600)
    expected_energy = site_data["Expected Power"].sum() * (df_timedelta.seconds / 3600)
    total_curtailment_duration = curtailment_df["Duration (h)"].sum()


    df_dict = {"Exported Energy (MWh)": round(exported_energy/1000,2),
               "Curtailed Energy (MWh)": round(total_curtailment_loss/1000,2),
               "Potential Energy (MWh)": round((exported_energy + total_curtailment_loss)/1000, 2),
               "Expected Energy (MWh)": round(expected_energy/1000, 2),
               "Total Curtailment time": round(total_curtailment_duration, 2)}

    curtailment_summary = pd.DataFrame.from_dict(df_dict, orient="index", columns=[site])


    return curtailment_df, site_data, total_curtailment_loss, curtailment_summary