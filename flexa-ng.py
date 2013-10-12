#!/usr/bin/env python3

import argparse
import sys
import os
import getpass
import configparser

import crypto
import tools

def usage():
    """Generate user help and parser user choices"""

    parser = argparse.ArgumentParser(
            description='A New Flexible and Distributed File System')
    #The following options are mutually exclusive
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-p', '--put', metavar='FILE', nargs='+',
            help='send file to server')
    group.add_argument('-g', '--get', metavar='FILE', nargs='+',
            help='receive file from server')
    group.add_argument('-l', '--list', metavar='PATH', nargs='?',
            help='list files from server')
    group.add_argument('-n', '--newkey', action='store_true',
            help='generate new user key')
    #This option can be used in combination with any other
    parser.add_argument('-v', '--verbose', action='count', default=0,
            help='increase output verbosity')

    return parser

def main():
    """The function called when this program is executed"""

    default_config = """
    #All network configuration goes here
    [Network]
        interface
        hostname
        port
        netmask
    #User related configuration
    [User]
        private key
    """

    #Read user configuration
    config_path = 'flexa-ng.ini'
    config = configparser.SafeConfigParser(allow_no_value=True)
    config.read_string(default_config)
    config.read(config_path)

    #If no option is given, show help and exit
    parser = usage()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)

    #Parse the user choices
    args = parser.parse_args()

    #Generate a new user key
    if args.newkey:
        #Checks if the user already has a key
        if config.get('User', 'private key'):
            confirm = tools.query_yes_no("There is already a generated key, "
                    "generate another one?", default='no')
            if not confirm:
                sys.exit(2)
        #Ask the desired name and password to the file
        try:
            filename = input('Filename? ')
        except KeyboardInterrupt:
            sys.exit(2)
        if not filename:
            sys.exit('Needs a filename!')
        filename = os.path.abspath(filename)
        try:
            password = getpass.getpass('Password? ')
        except KeyboardInterrupt:
            sys.exit(2)
        #Generate the RSA key and store it's path on config file
        crypto.generate_rsa_key(filename, password)
        config.set('User', 'private key', filename)
        print('RSA key generated!')

    #Write configuration file
    with open(config_path, 'w') as outfile:
        config.write(outfile)

if __name__ == '__main__':
    main()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
