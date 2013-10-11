#!/usr/bin/env python3

import argparse
import sys
import os

import file_man
import tools

#Python 2.x and 3.x compatibility
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

#Fix for Python 2 old 'raw_input'
try:
    import __builtin__
    input = getattr(__builtin__, 'raw_input')
except (ImportError, AttributeError):
    pass

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

def default_config(config):
    config.add_section('Network')
    config.set('Network', 'interface', 'None')
    config.set('Network', 'hostname', 'None')
    config.set('Network', 'port', 'None')
    config.set('Network', 'netmask', 'None')

    config.add_section('User')
    config.set('User', 'private key', 'None')

    return config

if __name__ == '__main__':
    #Read user configuration
    config_path = 'flexa-ng.ini'
    config = configparser.SafeConfigParser()
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        config = default_config(config)

    #If no option is given, show help and exit
    parser = usage()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(2)

    #Parse the user choices
    args = parser.parse_args()

    #Generate a new user key
    if args.newkey:
        if config.has_option('User', 'private key'):
            confirm = tools.query_yes_no("There is already a generated key, "
                    "generate another one?", default='no')
            if not confirm:
                sys.exit(2)
        filename = input('Filename? ')
        filename = os.path.abspath(filename)
        if not filename:
            sys.exit('Needs a filename!')
        password = input('Password? ')
        file_man.generate_rsa_key(filename, password)
        config.set('User', 'private key', filename)
        print('RSA key generated!')

    #Write configuration file
    with open(config_path, 'w') as outfile:
        config.write(outfile)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4