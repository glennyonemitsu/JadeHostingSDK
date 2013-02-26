import argparse 
import os
import os.path
import shutil
import sys


def create(args):
    location = os.path.abspath(args.create)
    sdk_location = os.path.join(location, '.sdk')
    if os.path.exists(sdk_location):
        print 'Directory %s already exists' % location
        sys.exit(1)
    else:
        print 'Creating project'
        if not os.path.exists(location):
            os.mkdir(location, 0755)
        print 'Creating SDK metadata directory %s' % sdk_location
        os.mkdir(sdk_location, 0755)
            

parser = argparse.ArgumentParser(description='SDK')
sub_parsers = parser.add_subparsers(help='Sub command help')

create_parser = sub_parsers.add_parser('create', help='Create a new project at specified directory')
create_parser.add_argument('-p', '--path', dest='path', metavar='PATH')
create_parser.set_defaults(callback=create)

server_parser = sub_parsers.add_parser('run_server', help='Run server')
server_parser.add_argument('-a', '--address', dest='host', metavar='HOST')
server_parser.add_argument('-p', '--port', dest='port', metavar='PORT')

args = parser.parse_args()
args.callback(args)

