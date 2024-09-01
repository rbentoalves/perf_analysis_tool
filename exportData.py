import pandas as pd
import os
from glob import glob


def create_Event_Tracker(df_all_incidents, site, all_curtailment_df):

    df_approved_incidents = df_all_incidents[~(df_all_incidents["Approved"].isna())]

    general_folder = glob(os.path.join(os.getcwd(), 'Results', site))[0]
    print(general_folder)
    event_tracker_path = general_folder + "/Event Tracker " + site + ".xlsx"

    writer = pd.ExcelWriter(event_tracker_path, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}})
    workbook = writer.book

    df_all_incidents.to_excel(writer, sheet_name='Incidents', index=False)
    df_approved_incidents.to_excel(writer, sheet_name='Approved Incidents', index=False)
    all_curtailment_df.to_excel(writer, sheet_name='Curtailment incidents', index=False)

    writer.close()

    writer.handles = None

    print('Done')


    return


def create_curtailment_file(site, curtailment_df, analysis_start_ts, analysis_end_ts):
    general_folder = glob(os.path.join(os.getcwd(), 'Results', site))[0]
    curtailment_file_path = (general_folder + "/Curtailment " + site + "_" + str(analysis_start_ts.date()) + "_to_" +
                             str(analysis_end_ts.date()) + ".xlsx")

    writer = pd.ExcelWriter(curtailment_file_path, engine='xlsxwriter',
                            engine_kwargs={'options': {'nan_inf_to_errors': True}})
    workbook = writer.book
    curtailment_df.to_excel(writer, sheet_name='Curtailment incidents', index=False)

    writer.close()

    writer.handles = None

    print('Done')


    return