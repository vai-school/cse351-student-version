"""
Course    : CSE 351
Assignment: 04
Student   : <Robert Lunden Vaile>

Instructions:
    - review instructions in the course

In order to retrieve a weather record from the server, Use the URL:

f'{TOP_API_URL}/record/{name}/{recno}

where:

name: name of the city
recno: record number starting from 0

"""

import threading
import time
import random
from common import *

from cse351 import *

THREADS = 200                # TODO - set for your program
WORKERS = 100                 # TODO - set for your program
RECORDS_TO_RETRIEVE = 5000  # Don't change


# ---------------------------------------------------------------------------
def retrieve_weather_data(queue1, queue2, spaces1, items1, spaces2, items2):
    while True:
        items1.acquire()
        item = queue1.get()
        if item is None:
            spaces1.release()
            break
        spaces1.release()
        name, recno = item
        result = get_data_from_server(f'{TOP_API_URL}/record/{name}/{recno}')
        spaces2.acquire()
        queue2.put((name, result['date'], result['temp']))
        items2.release()


# ---------------------------------------------------------------------------
# TODO - Create Worker threaded class
class Worker(threading.Thread):

    def __init__(self, queue2, noaa, spaces, items):
        threading.Thread.__init__(self)
        self.queue2 = queue2
        self.noaa = noaa
        self.spaces = spaces
        self.items = items

    def run(self):
        while True:
            self.items.acquire()
            item = self.queue2.get()
            if item is None:
                self.spaces.release()
                break
            city, date, temp = item
            self.noaa.add_record(city, date, temp)
            self.spaces.release()



# ---------------------------------------------------------------------------
# TODO - Complete this class
class NOAA:

    def __init__(self):
        self.data = {} #the dictionary that holds cities and temps
        self.lock = threading.Lock() #THE LOCK

    def add_record(self, city, date, temp):
        with self.lock: #Where the LOCK is
            if city not in self.data: #adds city to dictionary if its not there
                self.data[city] = [] 
            self.data[city].append(temp) #adds the temps to the city

    def get_temp_details(self, city):
        temps = self.data[city]
        average = sum(temps)/len(temps) #gets the average of the temps for the city
        return average


# ---------------------------------------------------------------------------
class Queue351():
    """ This is the queue object to use for this class. Do not modify!! """

    def __init__(self):
        self.__items = []
   
    def put(self, item):
        assert len(self.__items) <= 10
        self.__items.append(item)

    def get(self):
        return self.__items.pop(0)

    def get_size(self):
        """ Return the size of the queue like queue.Queue does -> Approx size """
        extra = 1 if random.randint(1, 50) == 1 else 0
        if extra > 0:
            extra *= -1 if random.randint(1, 2) == 1 else 1
        return len(self.__items) + extra


# ---------------------------------------------------------------------------
def verify_noaa_results(noaa):

    answers = {
        'sandiego': 14.5004,
        'philadelphia': 14.865,
        'san_antonio': 14.638,
        'san_jose': 14.5756,
        'new_york': 14.6472,
        'houston': 14.591,
        'dallas': 14.835,
        'chicago': 14.6584,
        'los_angeles': 15.2346,
        'phoenix': 12.4404,
    }

    print()
    print('NOAA Results: Verifying Results')
    print('===================================')
    for name in CITIES:
        answer = answers[name]
        avg = noaa.get_temp_details(name)

        if abs(avg - answer) > 0.00001:
            msg = f'FAILED  Expected {answer}'
        else:
            msg = f'PASSED'
        print(f'{name:>15}: {avg:<10} {msg}')
    print('===================================')


# ---------------------------------------------------------------------------
def main():

    log = Log(show_terminal=True, filename_log='assignment.log')
    log.start_timer()

    noaa = NOAA()

    # Start server
    data = get_data_from_server(f'{TOP_API_URL}/start')

    # Get all cities number of records
    print('Retrieving city details')
    city_details = {}
    name = 'City'
    print(f'{name:>15}: Records')
    print('===================================')
    for name in CITIES:
        city_details[name] = get_data_from_server(f'{TOP_API_URL}/city/{name}')
        print(f'{name:>15}: Records = {city_details[name]['records']:,}')
    print('===================================')

    records = RECORDS_TO_RETRIEVE

    # TODO - Create any queues, semaphores, locks or barriers you need
    queue1 = Queue351()
    queue2 = Queue351()

    spaces1 = threading.Semaphore(10)
    items1 = threading.Semaphore(0)
    spaces2 = threading.Semaphore(10)
    items2 = threading.Semaphore(0)

    workers = []
    threads = []

    for _ in range(WORKERS):
        w = Worker(queue2, noaa, spaces2, items2)
        w.start()
        workers.append(w)

    for _ in range(THREADS):
        t = threading.Thread(target=retrieve_weather_data, args=(queue1, queue2, spaces1, items1, spaces2, items2))
        t.start()
        threads.append(t)

    for name in CITIES:
        for i in range(records):
            spaces1.acquire()
            queue1.put((name, i))
            items1.release()

    for _ in range(THREADS):
        spaces1.acquire()
        queue1.put(None)
        items1.release()

    for t in threads:
        t.join()

    for _ in range(WORKERS):
        spaces2.acquire()
        queue2.put(None)
        items2.release()

    for w in workers:
        w.join()

    # End server - don't change below
    data = get_data_from_server(f'{TOP_API_URL}/end')
    print(data)

    verify_noaa_results(noaa)

    log.stop_timer('Run time: ')


if __name__ == '__main__':
    main()

