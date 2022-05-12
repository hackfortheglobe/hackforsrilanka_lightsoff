from pandas import read_excel
import os
from numpy import nan
from tqdm import tqdm
from lightsoff.models import DistrictPlace

path = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(path, "datafile/areas-district-table-may-12-2022.csv.xlsx")

def run():
    dataframe = read_excel(file_name, engine='openpyxl')
    dataframe = dataframe.replace(nan, '', regex=True)
    with tqdm(total=len(dataframe.index)) as pbar:
        for index, row_data in dataframe.iterrows():
            gss = row_data.get("gss")
            area = row_data.get("area")
            district = row_data.get("district")
            district_obj = DistrictPlace.objects.filter(district__iexact=district,
                                                    gss__iexact=gss,
                                                    area__iexact=area).first()
            pbar.set_description("Processing")
            pbar.update()
            if district_obj:
                continue
            DistrictPlace.objects.create(district=district,
                                       gss=gss,
                                       area=area)

