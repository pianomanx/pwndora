#Local modules
from logging import exception
from NetworkScanner import Network_Scanner

from ipaddress import ip_address
from loguru import logger
from datetime import datetime

import queue
import sys
import threading

from Connect import database_connect

class Thread_Scanner():
    def __init__(self,start,end,threads,timeout,screenshot):
        self.timeout = timeout
        self.screenshot = screenshot
        #self.targets = self.get_ranges(start, end)
        self.targets = self.get_ranges(start,end)
        self.threads = threads
        self.connection = database_connect()

    def set_ports(self,ports):
        self.ports = ports

    def get_ranges(self,start,end):
        #Get total of ip addresses
        start_int = int(ip_address(start).packed.hex(), 16)
        end_int = int(ip_address(end).packed.hex(), 16)
        return [ip_address(ip).exploded for ip in range(start_int, end_int)]

    def job(self,q):
        pool_sema.acquire()
        try:
            while not q.empty():
                ip = q.get()
                Scanner = Network_Scanner(ip)
                Scanner.set_connection(self.connection)
                Scanner.start(self.timeout,self.screenshot,self.ports)
                q.task_done()
        finally:
            pool_sema.release()

    def start_threads(self):
        #Implemeting Queue, safe threading
        logger.info("Searching connected devices, please wait")
        start = datetime.now()
        q = queue.Queue()
        #Semaphore object limit max number of threads in paralell
        global pool_sema
        pool_sema = threading.Semaphore(value=900)
        try:
            logger.info("Launching threads")
            for j in self.targets:
                q.put(j)
                
            logger.info("Waiting for Queue to complete, {} jobs".format(q.qsize()))
    
            for i in range(self.threads):
                thread = threading.Thread(target=self.job, args=(q,),daemon=True)
                thread.start()
            q.join()
            end = datetime.now()
            elapsed = end-start
            logger.info("Execution time: {}".format(elapsed))

        except KeyboardInterrupt:
            logger.info("You pressed CTRL+C")
            sys.exit(1)