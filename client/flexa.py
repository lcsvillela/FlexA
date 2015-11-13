'''
Created on 15/12/2014

@author: mario
'''
# import class that set every configs
from client.config import Config
import crypto
import misc
import os
import sys
from entity import file
from client import rpc_client
from threading import Thread
from stat import S_ISREG
from itertools import cycle
from entity import user
import time
import logging

class ClientFile(object):
    filename = ''
    enc_filename = ''
    relative_filepath = ''
    absolute_filepath = ''
    absolute_enc_filepath = ''

class Client(object):
    '''
    classdocs
    '''
    
    # object that have every configs and parser
    configs = None

    inicio = time.time()

    rpc = rpc_client.RPC()


########################################################
########  CONTROLLING METHODS  #########################
########################################################


    def __init__(self):
        '''
        Constructor
        '''
        self.configs = Config()

        args = self.configs.args

        self.user = user.User()
        self.user.set_attr()

        # Send a file to server
        if args.put:
            self.logger = logging.getLogger("[Flexa_cli - send_file]")
            for filename in args.put:
                file_info = ClientFile()
                # this can be either here or in the set_file_info function
                #file_info.filename = os.path.normpath(filename)
                if self.set_file_info_to_send(file_info, filename):
                    self.send_file(file_info)

        # Get a file from server
        if args.get:
            self.logger = logging.getLogger("[Flexa_cli - recv_file]")
            for filename in args.get:
                file_info = ClientFile()
                file_info.filename = os.path.normpath(filename)
                if self.set_file_info_to_receive(file_info):
                    self.receive_file(file_info)

        if args.list:
            self.logger = logging.getLogger("[Flexa_cli - list_file]")
            self.list_files()

        if args.delete:
            for filename in args.delete:
                self.delete_file(filename)
                
        # Write configuration file
        with open(self.configs._config_filepath, mode='w', encoding='utf-8') as outfile:
            self.configs.loaded_config.write(outfile)

        fim = time.time()
        
        print(fim - self.inicio)

    def set_file_info_to_receive(self, file_info):
        file_info.absolute_filepath = os.path.join(self.configs._current_local_dir, file_info.filename)
        file_info.absolute_filepath = os.path.normpath(file_info.absolute_filepath)
        file_info.relative_filepath = os.path.join(self.configs._current_relative_dir, file_info.filename)
        file_info.relative_filepath = os.path.normpath(file_info.relative_filepath)

        #verify if it's withing FlexA data directory
        if not self.configs._data_dir in file_info.absolute_filepath:
            print("Skipping '" + file_info.absolute_filepath + "'. "
                    "File can't be located outside mapped directory")
            return False

        file_info.enc_filename = file_info.filename + '.enc'
        file_info.absolute_enc_filepath = file_info.absolute_filepath + '.enc'
        return True

    def set_file_info_to_send(self, file_info, filename):
        """ If the given filename exists, is a regular file and is inside
            the mapped directory tracked by FlexA, this function:
             -Finds names relative to FlexA system and absolute pathnames
                for local file system

            Parameters:
                file_info - object to store some info about the path in
                    different environments (FlexA dir or local one)
                filename - name of file that will be process
        """
        # local full filepath
        file_info.absolute_filepath = os.path.abspath(filename)

        # verify if path exists
        if not os.path.exists(file_info.absolute_filepath):
            print("Skipping '" + file_info.absolute_filepath + "'. "
                  "File was not found.")
            return False
        # verify if it's a regular file
        elif not self.is_file(file_info.absolute_filepath):
            print("Skipping '" + file_info.absolute_filepath + "'. "
                  "It's not a path to a regular file.")
            return False
        #verify if it's withing FlexA data directory
        elif not self.configs._data_dir in file_info.absolute_filepath:
            print("Skipping '" + file_info.absolute_filepath + "'. "
                    "File can't be located outside mapped directory")
            return False

        # full filepath relative to FlexA file system
        file_info.relative_filepath = file_info.absolute_filepath.split(self.configs._current_local_dir)[1]

        file_info.filename = file_info.relative_filepath.split('/')[-1]

        # name of encrypted file
        file_info.enc_filename = file_info.filename + ".enc"

        # full local filepath for the encrypted file (temporary to send and receive)
        file_info.absolute_enc_filepath = file_info.absolute_filepath + ".enc"

        return True

    def send_file_part(self, num_part, ip_server, port_server, abs_enc_filepath):

        host = (ip_server, port_server)
        local_file_name_complete = abs_enc_filepath + '.' + str(num_part)
        # TODO: colocar um if no send_file para confirmar se o envio foi efetuado com sucesso
        misc.send_file(host, local_file_name_complete)
        os.remove(local_file_name_complete)

    def check_is_file(self, pathname):
        return S_ISREG(os.stat(pathname).st_mode)

    def is_file(self, pathname):
        return S_ISREG(os.stat(pathname).st_mode)


########################################################
#########   OPERATIONS METHODS   #######################
########################################################

        
    def send_file(self, file_info):
        """
        send file from client to server
        """

        # verify if this file exist (same name in this directory)
        dir_key = "/"  # FIXME set where is.... need more discussion
        f_name = file_info.relative_filepath
        f_size=os.path.getsize(file_info.absolute_filepath)
        file_obj = file.File(name=f_name, user_id=self.user.uid,
                             size=f_size, num_parts=3)

        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.user.primary_servers])

        #Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))
        # ask to server if is update or new file

        salt = server_conn.get_salt( file_obj.name, file_obj.user_id)
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        crypto.encrypt_file(read_key, file_info.absolute_filepath, file_info.absolute_enc_filepath, 16)
        # verify if exist file

        if not ( misc.split_file(file_info.absolute_enc_filepath, file_obj.num_parts) ):
            sys.exit("Problems while splitting file.\nTry again.")

        # if salt has a value then is update. because server return a valid salt
        if salt:
            for num_part in range( file_obj.num_parts ):
                port_server = server_conn.update_file( file_obj, num_part, self.user.primary_servers )
                if port_server == False:
                    sys.exit("Some error occurred. Maybe you don't have permission to \
                            write. \nTry again.")
                self.send_file_part( num_part, self.rpc.ip_server, port_server, file_info.absolute_enc_filepath )
                server_conn = self.rpc.set_server(next(server_cycle))
        else:
            # server return port where will wait a file
            for num_part in range(file_obj.num_parts):
                self.logger.info("Send new file: part {} to server {}".format(num_part, self.rpc.ip_server))
                port_server = server_conn.negotiate_store_part(file_obj, dir_key, num_part, self.user.primary_servers)
                if not port_server:
                    sys.exit("Some error occurred. Maybe you don't have permission to write. \nTry again.")
                self.send_file_part(num_part, self.rpc.ip_server, port_server, file_info.absolute_enc_filepath)
                server_conn = self.rpc.set_server(next(server_cycle))

        # remove temp crypt file
        os.remove(file_info.absolute_enc_filepath)


    def receive_file(self, file_info):
        """
        receive file from server
        """

        port, sock = misc.port_using(4001)

        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.user.primary_servers])
        #Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))

        salt = server_conn.get_salt(file_info.relative_filepath, self.user.uid)

        if (salt == 0):
            print("This file can't be found")
            return

        file_obj = file.File()
        read_key = file_obj.set_keys(self.configs.loaded_config.get("User", "private key"), salt)

        total_parts_file = 3  # FIXME: colocar para descobrir automaticamante numero de partes
        name_parts_file = []
        
        for num_part in range(total_parts_file):
            name_file = file_info.absolute_enc_filepath + '.' + str(num_part)
            name_parts_file.append(name_file)
            # make a thread that will receive file in socket
            thr = Thread(target=misc.receive_file, args=(sock, name_file))
            thr.start()
            # ask to server a file with name (keys[0] = hash)
            # client ip and your port to receive file
            if ( server_conn.give_file( misc.my_ip(),port, file_obj.verify_key, num_part) ):
                # exit with error and kill thread thr
                sys.exit("An error occured. Try again later.")
            thr.join()
            server_conn = self.rpc.set_server(next(server_cycle))

        misc.join_file(name_parts_file, file_info.enc_filename)

        crypto.decrypt_file(read_key, file_info.enc_filename, file_info.absolute_filepath, 16)

        #remove temp files from  workstation -> parts
        for file_to_rm in name_parts_file:
            os.remove(file_to_rm)
        #remove temp files from  workstation -> complete
        os.remove(file_info.absolute_enc_filepath)

    def list_files(self):
        """
        Search every file from verify_key
            verify_key is directory where called this operation - answer is a dictionary of files and yours attributes 
        """
        #server_conn = self.rpc.get_next_server()
        #make list of server ip (without uid) be a circular list
        server_cycle = cycle([item[1] for item in self.user.primary_servers])
        #Use variable primary_servers -> [ [uid,ip], [uid,ip] ... ]
        server_conn = self.rpc.set_server(next(server_cycle))

        # just to clean a bit these huge var names
        cur_dir = self.configs._current_relative_dir
        file_dictionaries = server_conn.list_files(cur_dir, self.user.uid)

        columns = file_dictionaries[0].keys()
        
        all_widths = []
        for file_dict in file_dictionaries:
            all_widths.append([len(v) for v in file_dict.values()])
        
        widths = [max(row_lenghts) for row_lenghts in zip(*all_widths)]
        header = dict(zip(columns, widths))
        
        
        print("Created on".ljust(header["create_date"]), end="  ")
        print("Last modified on".ljust(header["modify_date"]), end="  ")
        print("Size".ljust(header["size"]), end="  ")
        print("Name".ljust(header["name"]))
        
        # print info for every file
        for file_dict in file_dictionaries:
            # check if it's within current directory
            if cur_dir != os.path.dirname(file_dict['name']):
                #print("-".ljust(header["create_date"]), end="  ")
                #print("-".ljust(header["modify_date"]), end="  ")
                #print("-".ljust(header["size"]), end="  ")
                #print(file_dict["name"].ljust(header["name"])) TODO parse the name
                continue

            print(file_dict["create_date"].ljust(header["create_date"]), end="  ")
            print(file_dict["modify_date"].ljust(header["modify_date"]), end="  ")
            print(file_dict["size"].ljust(header["size"]), end="  ")
            print(file_dict["name"].ljust(header["name"]))
            
        #else: # check if current dir is substring at the beginning
        #    if not os.path.dirname(dic_file['name']).startswith(cur_dir):
        #        continue

    def delete_file(self, name_file):
        """
            Delete files in flexa system

            Parameters:
                name_file - name of file
        """

        pass
