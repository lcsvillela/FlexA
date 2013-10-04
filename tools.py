#!/usr/bin/env python3

"""Provide general tools to FlexA."""

import os
import sys
import re
import string
import subprocess
import sqlite3
from threading import Thread

__authors__ = ["Thiago Kenji Okada", "Leandro Moreira Barbosa"]

class Ping(Thread):
    """Class to send Ping messages to network nodes

    Public variables:
    received -- count of received packages
    minimum -- minimum RTT from Ping
    average -- average RTT from Ping
    maximum -- maximum RTT from Ping
    jitter -- RTT variation from Ping

    """

    received = None
    minimum = None
    average = None
    maximum = None
    jitter = None

    def __init__(self, host, count=4):
        """Ping constructor

        Input parameters:
        host -- hostname/IP address of the target node
        count -- number of ping messages; default is 4

        """
        Thread.__init__(self)
        self.__host = host
        self.__count = count

    def run(self):
        """Runs the ping thread, if there is no answer the thread is finished.

        """

        # Only Linux platform for now, using ping from iputils
        if sys.platform == 'linux' or sys.platform == 'linux2':
            lifeline = r'(\d) received'
            ping_regex = r'(\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)'

        ping = subprocess.Popen(
            ["ping", "-c", str(self.__count), self.__host],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

        while True:
            try:
                out, err = ping.communicate()
            except ValueError:
                break
            # Pega o número de pacotes que foram retornados
            matcher = re.compile(lifeline)
            self.received = re.findall(lifeline, str(out))
            # Pega as informações geradas pelo ping
            matcher = re.compile(ping_regex)
            self.minimum, self.average, self.maximum, self.jitter = \
            matcher.search(str(out)).groups()

class ConfigDat:
    """Class to manipulate configuration files

    Public variables:
    interface -- network interface from machine
    hostname -- IP/hostname from machine
    port -- port used on machine
    netmask -- netmask from machine

    """
    interface = ''
    hostname = ''
    port = ''
    netmask = ''

    def __init__(self, filepath='flexa.dat'):
        """Construtor da classe ConfigDat

        Parâmetros de entrada:
        filepath -- filepath to the configuration file

        """
        self.__filepath = filepath

        if os.path.exists(self.__filepath):
            self.load()
        else:
            self.default_config()

    def load(self):
        """(Re)load configuration file"""

        # Using the following pattern: <option: value>
        regex = re.compile("\S+:.+$")
        result = []

        with open(self.__filepath, 'r') as infile:
            for line in infile:
                aux = regex.match(line)
                if aux:
                    result.append(aux.group(0).split(":"))

        for attr, value in result:
            setattr(self, attr.strip(), value.strip())

    def save(self, filepath=None):
        """Save config file

        Input paramters:
        filepath -- saves config file in another place

        """

        if not filepath:
            filepath = self.__filepath

        options = [('interface', self.interface),
                  ('hostname', self.hostname),
                  ('port', self.port),
                  ('netmask', self.netmask)]

        with open(filepath, 'w') as outfile:
            for i in options:
                outfile.write('{}: {}\n'.format(*i))

    def default_config(self):
        """Generate default configuration"""

        interface = None
        hostname = None
        port = None
        netmask = None


class DataBase:

    def __init__(self, filepath):
        newdb = True
        if os.path.exists(filepath): newdb = False

        self.__conn = sqlite3.connect(filepath)
        self.__db = self.__conn.cursor()

        if newdb:
            # TODO: DB prototype
            query = ("CREATE TABLE file_table (file_uuid VARCHAR "
            "PRIMARY KEY, hash_file VARCHAR, filepath VARCHAR "
            "folder VARCHAR, user_uuid VARCHAR, proprierties VARCHAR, "
            "id_ver INTEGER, chunks VARCHAR)")
            self.__db.execute(query)

    def __enter__(self):
        return self

    def add_file(self, file_uuid, hash_file, filepath,
            folder, user_uuid, proprierties, id_ver, chunks):
        query = ("INSERT INTO file_table VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        param = (file_uuid, hash_file, filepath, folder, user_uuid,
                proprierties, id_ver, chunks)
        self.__db.execute(query, param)
        self.__conn.commit()

    def remove_file(self, hash_file):
        query = ("DELETE FROM file_table WHERE hash_file = ?")
        param = (file_uuid,)
        self.__db.execute(query, param)
        self.__conn.commit()

    def info_file(self, hash_file):
        query = ("SELECT * from file_table WHERE hash_file = ?")
        param = (file_uuid,)
        self.__db.execute(query, param)
        return self.__db.fetchone()

    def list_files(self, user_uuid):
        query = ("SELECT filepath from file_table WHERE user_uuid = ?")
        param = (user_uuid,)
        self.__db.execute(query, param)
        return self.__db.fetchall()

    def save(self):
        self.__conn.commit()

    def __exit__(self):
        self.save()
        self.__conn.close(self, exc_type, exc_value, traceback)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4