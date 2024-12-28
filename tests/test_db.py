from libs.database.database import Database, Roast, GasData
from datetime import datetime
import pandas as pd

db = Database()
db.initTables()
db.initSession()

roastId = db.insertRoast(roast=Roast(None, Roast.BeanType.Arabica, Roast.RoastLevel.Light, None, None, datetime.now(), datetime.now()))
gasDataId = db.insertGasData(gas_data=GasData(None, roastId, 0, 1, 2, 3, 4, 5, 6, 7, datetime.now(), datetime.now()))

print(
f'''
inserted : 
roastId : {roastId}
gasDataId : {gasDataId}
''')

gas_datas :  pd.DataFrame = pd.DataFrame()
gas_datas["MQ135"] = [1, 2]
gas_datas["MQ136"] = [2, 3]
gas_datas["MQ137"] = [2, 3]
gas_datas["MQ138"] = [2, 3]
gas_datas["MQ2"] = [2, 3]
gas_datas["MQ3"] = [2, 3]
gas_datas["TGS822"] = [2, 3]
gas_datas["TGS2620"] = [2, 3]

def gasDFtoJson(datas : pd.DataFrame):
    mq136 = datas.iloc[:,0].to_list()
    mq135 = datas.iloc[:,1].to_list()
    mq137 = datas.iloc[:,2].to_list()
    mq138 = datas.iloc[:,3].to_list()
    mq2 = datas.iloc[:,4].to_list()
    mq3 = datas.iloc[:,5].to_list()
    tgs822 = datas.iloc[:,6].to_list()
    tgs2620 = datas.iloc[:,7].to_list()

    return {
        "mq136" : mq136,
        "mq135" : mq135,
        "mq137" : mq137,
        "mq138" : mq138,
        "mq2" : mq2,
        "mq3" : mq3,
        "tgs822" : tgs822,
        "tgs2620" : tgs2620
    }

result = gasDFtoJson(gas_datas)

print(result)

