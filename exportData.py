import pandas as pd
import os
from glob import glob


def create_Event_Tracker(df_all_incidents, site):
    general_folder = glob(os.path.join(os.getcwd(), 'Results', site))[0]
    print(general_folder)
    event_tracker_path = general_folder + "/Event Tracker " + site + ".xlsx"

    writer = pd.ExcelWriter(event_tracker_path, engine='xlsxwriter', engine_kwargs={'options': {'nan_inf_to_errors': True}})
    workbook = writer.book

    df_all_incidents.to_excel(writer, sheet_name='Incidents', index=False)

    writer.close()

    writer.handles = None

    print('Done')


    return event_tracker_path