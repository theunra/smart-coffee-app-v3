from libs.e_nose.serial_handler import SerialHandler

from datetime import datetime

class Predict():
    def __init__(self):
        pass

    def predict(self, data):
        pass

    def resetPredict(self):
        pass

def onSerialDataReceive(data):
    print(data)

def testListenSerialData():
    port = SerialHandler.findPort("ESP32")

    print("[Enose] Connecting to serial port : " + port.device)
    serialHandler = SerialHandler(port=port.device, baud=115200)

    serialHandler.startListening(target=onSerialDataReceive)


class Enose:
    def __init__(
            self, port = None, 
            classifier = Predict()
            ) -> None:

        self.getPort(port)

        self.serialHandler = SerialHandler(port=self.port, baud=115200)
        self.classifier = classifier

        self.datas = [] # List of enose json data , each json has 8 adc sensor data

        self.is_run = False

        self.__onPredictionDone = None
        self.__onPredictionDoneArgs = ()

    def getPort(self, port):
        if(port == None):
            self.port = SerialHandler.findPort("ESP32")
            
            if(self.port == False):
                raise Exception("ESP32 port not found")
            else:
                self.port = self.port.device
        
        else:
            self.port = port

    def onPredictionDone(self, target=None, args=()):
        self.__onPredictionDone = target
        self.__onPredictionDoneArgs = args

    def onReceiveSerialData(self, data):
        # raise NotImplementedError
        #append time
        t = datetime.now()
        data["time"] = str(t)
        
        self.classifier.predict(data)
        
        self.datas.append(data)

    def jsonEnoseADCDataToArray(self, datas : list):
        arr = []
        for d in datas:
            arr.append(d["adc_mq135"])
            # arr.append(d["adc_mq136"])
            arr.append(d["adc_mq137"])
            arr.append(d["adc_mq138"])
            # arr.append(d["adc_mq2"])
            arr.append(d["adc_mq3"])
            # arr.append(d["adc_tgs822"])
            # arr.append(d["adc_tgs2620"])
        return arr

    def start(self):
        print("[Enose] starting...")
        
        if(self.__onPredictionDone == None):
            raise Exception("[Enose] onPredictionDone callback cant be None")
        
        self.is_run = True
        self.serialHandler.startListening(target=Enose.onReceiveSerialData, args=(self,))
        print("[Enose] started")
    
    def stop(self):
        print("[Enose] stopping...")
        self.is_run = False
        self.serialHandler.stopListening()
        print("[Enose] stop")

    def reset(self):
        self.classifier.resetPredict()
        self.datas.clear()
