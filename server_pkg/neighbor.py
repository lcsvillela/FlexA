'''
Created on 24/07/2015

@author: mario
'''

import hashlib
from time import sleep
import binascii
from server_pkg.server import Server
import multiprocessing
from server_pkg.RPC import RPC
import logging

class Neighbor():
    """
    Class dedicate to monitoring neighbors servers
    """

    #indicate how many machines will be observed -> 2 in right and 2 in left
    window_size = 4

    #interval between scans to verify if server is online (seconds)
    TIME_AUTO_SCAN =3

    #array to save neighbors - [[uid,ip]]
    left_neighbor = []
    right_neighbor = []
    
    UPDATE = multiprocessing.Event()

    def __init__(self):
        self.logger = logging.getLogger("[Sync Server - Neighbor]")

        self.server_obj = RPC()
        self.server_obj.scan_ping.LOCAL = True

        self.zero_map()

    def zero_map(self):
        self.left_neighbor = []
        self.right_neighbor = []
        for _ in range(self.window_size//2):
            self.left_neighbor.append(["0",0])
            self.right_neighbor.append(["0",0])

    def daemon(self):
        """
            Resposable to start auto scan in network in new process
        """

        proc = multiprocessing.Process(target=self.auto_scan, daemon=True)
        proc.start()

    def auto_scan(self):
        """
            Make scan in network to verify if servers is online
        """
        self.first_searcher()
        last_hash=b'0'
        count=5
        while True:
            self.verify_map()
            count-=1
            if(count<=0 or self.UPDATE.is_set()):
                self.UPDATE.clear()
                count=5
                self.first_searcher()
                hash = hashlib.md5()
                hash.update( binascii.a2b_qp(str(self.get_neighbors())) )
                if(last_hash != hash.digest()):
                    self.logger.debug("Update map all servers")
                    self.update_all()
                    last_hash=hash.digest()
            sleep(self.TIME_AUTO_SCAN)

    def update_all(self):
        for server in (self.left_neighbor+self.right_neighbor):
            if(server[1]!=0):
                server_conn = self.server_obj.set_server(ip=server[1])
                try:
                    server_conn.update_neighbor()
                except:
                    self.count=0

    def verify_map(self):
        """
            Make a verify if servers is online in current map, if some one is offline try to find next
        """

        for server in self.get_neighbors():
            server_conn = self.server_obj.set_server(ip=server[1])
            try:
                server_conn.still_alive()
            except:
                self.first_searcher()
                break

    def get_neighbors(self):
        #return a growing list of [uid, ips]
        return (self.left_neighbor[::-1]+[[Server.uid_hex,Server.ip]]+self.right_neighbor)

    def first_searcher(self):
        """
            Search in system who is your neighbor
            Used when system start or is unstable
        """
        #searching servers with ping
        server_conn = self.server_obj.get_next_server()
        map = server_conn.get_neighbor_map()

        #using the first map go to the next server
        #stop when find a map whose id can be placed in the middle
        # only one of the following while(s) will be executed
        while( (int(map[0][0],16)<Server.uid_int) and (map[0][0]!='0') ):
            server_conn = self.server_obj.set_server(map[0][1])
            map = server_conn.get_neighbor_map()

        while( (int(map[len(map)-1][0],16)>Server.uid_int) and
               (map[len(map)-1][0]!='0') ):
            server_conn = self.server_obj.set_server(map[(len(map)//2)-1][1])
            map = server_conn.get_neighbor_map()

        if('0' in dict(map)):
            self.zero_map()
            self.server_obj.scan_online_servers()
            #this is a signal that all machines just started or something went wrong -> verify all servers with ping
            for _ in range( len(self.server_obj.list_online) ):
                server_conn = self.server_obj.get_next_server()
                map = server_conn.get_neighbor_map()
                if(int(map[len(map)//2][0],16) < Server.uid_int):
                    #then this server is in left
                    self.put_in_left(map[len(map)//2])
                elif(int(map[len(map)//2][0],16) > Server.uid_int):
                    self.put_in_right(map[len(map)//2])
        else:
            #if find a map that your id can put in the middle
            for server in map:
                if(int(server[0],16) < Server.uid_int):
                    #then this server is in left
                    self.put_in_left(server)
                elif(int(map[len(map)//2][0],16) > Server.uid_int):
                    self.put_in_right(server)

        self.update_all()
        self.logger.debug(" Neighbors map:\n {}".format( str(self.get_neighbors()) ) )

    def put_in_left(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

            exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.left_neighbor[i] == server):
                break
            if(int(self.left_neighbor[i][0],16)<int(server[0],16)):
                #start to change vector
                aux_next, self.left_neighbor[i] = self.left_neighbor[i], aux_next

    def put_in_right(self, server):
        """insert server in left list
                -server is a vector [uid(hex),ip]

                exemple: left_neighbor=[[2,ip1][3,ip2]] server=[1,ip3] -> left_neighbor=[[1,ip3][2,ip1]]
        """
        aux_next = server
        for i in range(self.window_size//2):
            if(self.right_neighbor[i] == server):
                break
            if( (self.right_neighbor[i][0]=='0') or (int(self.right_neighbor[i][0],16)>int(server[0],16)) ):
                #start to change vector
                aux_next, self.right_neighbor[i] = self.right_neighbor[i], aux_next