import sqlite3
import datetime

class Values:
    def get(self): ...

class Session(Values):
    class Status:
        STOP = 0
        START = 1
        PAUSE = 2

    def __init__(self, id, roast_id, status, created_at, updated_at):
        super().__init__()
        self.id = id
        self.roast_id = roast_id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def get(self):
        return (self.id, self.roast_id, self.status, self.created_at, self.updated_at)

class Roast(Values):
    class BeanType:
        Arabica = 0
        Robusta = 1
    
    class RoastLevel:
        Light = 0
        Medium = 1
        Dark = 2
    
    def __init__(self, id, bean_type, roast_level, start_time, duration, created_at, updated_at):
        super().__init__()
        self.id = id
        self.bean_type = bean_type
        self.roast_level = roast_level
        self.start_time = start_time
        self.duration = duration
        self.created_at = created_at
        self.updated_at = updated_at

    def get(self):
        return (self.id, self.bean_type, self.roast_level, self.start_time, self.duration, self.created_at, self.updated_at)

class GasData(Values):
    def __init__(self, id, roast_id, mq135, mq136, mq137, mq138, mq2, mq3, tgs822, tgs2620, created_at, updated_at):
        super().__init__()
        self.id = id
        self.roast_id = roast_id
        self.mq135 = mq135
        self.mq136 = mq136
        self.mq137 = mq137
        self.mq138 = mq138
        self.mq2 = mq2
        self.mq3 = mq3
        self.tgs822 = tgs822
        self.tgs2620 = tgs2620
        self.created_at = created_at
        self.updated_at = updated_at

    def get(self):
        return (self.id, self.roast_id, self.mq135, self.mq136, self.mq137, self.mq138, self.mq2, self.mq3, self.tgs822, self.tgs2620, self.created_at, self.updated_at)

class VideoData(Values):
    def __init__(self, id, roast_id, frame, created_at, updated_at):
        super().__init__()
        self.id = id
        self.roast_id = roast_id
        self.frame = frame
        self.created_at = created_at
        self.updated_at = updated_at

    def get(self):
        return (self.id, self.roast_id, self.frame, self.created_at, self.updated_at)
    
class AudioData(Values):
    def __init__(self, id, roast_id, wav, created_at, updated_at):
        super().__init__()
        self.id = id
        self.roast_id = roast_id
        self.wav = wav
        self.created_at = created_at
        self.updated_at = updated_at

    def get(self):
        return (self.id, self.roast_id, self.wav, self.created_at, self.updated_at)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('roast-sense.db')

    def initTables(self):
        cursor = self.conn.cursor()

        # Create tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS session (
                       id           int         primary key, 
                       roast_id     int,                        
                       status       int                         not null,                       
                       created_at   timestamp                   not null,
                       updated_at   timestamp                   not null
                       );''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS roast (
                       id           int         primary key,                        
                       bean_type    int                         not null,
                       roast_level  int                         not null, 
                       start_time   timestamp,
                       duration     real,
                       created_at   timestamp                   not null,
                       updated_at   timestamp                   not null
                       );''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS gas_data (
                       id           int         primary key, 
                       roast_id     int                         not null, 
                       mq135        int,
                       mq136        int, 
                       mq137        int, 
                       mq138        int, 
                       mq2          int, 
                       mq3          int, 
                       tgs822       int, 
                       tgs2620      int,
                       created_at   timestamp                   not null,
                       updated_at   timestamp                   not null
                       );''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS video_data (
                       id           int         primary key, 
                       roast_id     int                         not null, 
                       frame        blob,
                       created_at   timestamp                   not null,
                       updated_at   timestamp                   not null
                       );''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS audio_data (
                       id           int         primary key, 
                       roast_id     int                         not null, 
                       wav          blob,
                       created_at   timestamp                   not null,
                       updated_at   timestamp                   not null
                       );''')
        

        cursor.execute('''CREATE TABLE IF NOT EXISTS video_data_temp (
                       id           int         primary key, 
                       roast_id     int                         not null, 
                       frame        blob,
                       created_at   timestamp                   not null,
                       updated_at   timestamp                   not null
                       );''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS audio_data_temp (
                       id           int         primary key, 
                       roast_id     int                         not null, 
                       wav          blob,
                       created_at   timestamp                   not null,
                       updated_at   timestamp                   not null
                       );''')
        
        self.conn.commit()

    def insert(self, query, values : Values):
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(query, values.get())

            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(e)
            isAlreadyInserted = str(e).find("UNIQUE")
            
            if(isAlreadyInserted > -1):
                print("Data is already inserted")

            else:
                raise e
            
        return cursor.lastrowid
                
    def initSession(self):
        session = Session(1, None, Session.Status.STOP, datetime.datetime.now(), datetime.datetime.now())

        self.insertSession(session=session)

    def insertSession(self, session : Session):
        query = ('''INSERT INTO session (id, roast_id, status, updated_at, created_at) values (?, ?, ?, ?, ?);''')

        return self.insert(query=query, values=session)

    def insertRoast(self, roast : Roast):
        query = ('''INSERT INTO roast (id, bean_type, roast_level, start_time, duration, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?);''')

        return self.insert(query=query, values=roast)

    def insertGasData(self, gas_data : GasData):
        query = ('''INSERT INTO gas_data (id, roast_id, mq135, mq136, mq137, mq138, mq2, mq3, tgs822, tgs2620, created_at, updated_at) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);''')

        return self.insert(query=query, values=gas_data)

    def insertVideoData(self, video_data : VideoData):
        query = ('''INSERT INTO video_data (id, roast_id, frame, created_at, updated_at) values (?, ?, ?, ?, ?);''')

        return self.insert(query=query, values=video_data)

    def insertAudioData(self, audio_data : AudioData):
        query = ('''INSERT INTO audio_data (id, roast_id, wav, created_at, updated_at) values (?, ?, ?, ?, ?);''')

        return self.insert(query=query, values=audio_data)
    
    def insertAudioDataTemp(self, audio_data : AudioData):
        query = ('''INSERT INTO audio_data_temp (id, roast_id, wav, created_at, updated_at) values (?, ?, ?, ?, ?);''')

        return self.insert(query=query, values=audio_data)
    
    def truncateAudioDataTemp(self):
        query = ('''TRUNCATE audio_data_temp;''')

        cursor = self.conn.cursor()

        try:
            cursor.execute(query)

            self.conn.commit()

        except sqlite3.IntegrityError as e:
            print(e)