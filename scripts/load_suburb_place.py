from pandas import read_excel
import os
from numpy import nan
from tqdm import tqdm
from lightsoff.models import SuburbPlace

path = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(path, "datafile/suburb-areas-places-may-04-2022-FINAL.xlsx")

def run():
    dataframe = read_excel(file_name, engine='openpyxl')
    dataframe = dataframe.replace(nan, '', regex=True)
    with tqdm(total=len(dataframe.index)) as pbar:
        for index, row_data in dataframe.iterrows():
            gss = row_data.get("gss")
            area = row_data.get("area")
            suburb = row_data.get("suburb")
            suburb_obj = SuburbPlace.objects.filter(suburb__iexact=suburb,
                                                    gss__iexact=gss,
                                                    area__iexact=area).first()
            pbar.set_description("Processing")
            pbar.update()
            if suburb_obj:
                continue
            SuburbPlace.objects.create(suburb=suburb,
                                       gss=gss,
                                       area=area)

