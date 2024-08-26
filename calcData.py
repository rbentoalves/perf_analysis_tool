import re


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
        active_hours = len(incident_irradiance) * (df_timedelta.seconds / 3600)
        energy_lost = (
                (incident_irradiance["Avg Irradiance POA"] * incident_irradiance["Budget PR"] / 1000).sum() * (
                    df_timedelta.seconds / 3600) * row["Capacity related component"])

        df_all_incidents.loc[index, "Duration (h)"] = duration
        df_all_incidents.loc[index, "Active hours (h)"] = active_hours
        df_all_incidents.loc[index, "Irradiation period"] = incident_irradiance_total
        df_all_incidents.loc[index, "Energy lost (kWh)"] = energy_lost
        df_all_incidents.loc[index, "Weighted downtime %"] = active_hours * (
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


def calculate_curtailment_losses(df_all_incidents, all_data_df, site, all_general_info, budget_pr, df_timedelta):
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
        active_hours = len(incident_irradiance) * (df_timedelta.seconds / 3600)
        energy_lost = (
                (incident_irradiance["Avg Irradiance POA"] * incident_irradiance["Budget PR"] / 1000).sum() * (
                    df_timedelta.seconds / 3600) * row["Capacity related component"])

        df_all_incidents.loc[index, "Duration (h)"] = duration
        df_all_incidents.loc[index, "Active hours (h)"] = active_hours
        df_all_incidents.loc[index, "Irradiation period"] = incident_irradiance_total
        df_all_incidents.loc[index, "Energy lost (kWh)"] = energy_lost
        df_all_incidents.loc[index, "Weighted downtime %"] = active_hours * (
                row["Capacity related component"] / site_capacity) / site_active_hours

    return df_all_incidents