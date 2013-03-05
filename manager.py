import argparse 

from sdklib import commands


parser = argparse.ArgumentParser(description='SDK')
sub_parsers = parser.add_subparsers(help='Sub commands for the manager script')

create_parser = sub_parsers.add_parser('create', help='Create a new project at specified directory')
create_parser.add_argument('-p', '--path', dest='path', metavar='PATH')
create_parser.add_argument('-b', '--bootstrap', action='store_true', help='Include the Twitter Bootstrap framework')
create_parser.set_defaults(callback=commands.create)

server_parser = sub_parsers.add_parser('run_server', help='Run server')
server_parser.add_argument(
    '-a', '--address', dest='address', metavar='ADDRESS', default='127.0.0.1:9000'
)
server_parser.add_argument(
    '-p', '--path', dest='path', metavar='PATH', default='.'
)
server_parser.set_defaults(callback=commands.run_server)

upload_parser = sub_parsers.add_parser('upload', help='Upload a new project at specified directory to the hosting account')
upload_parser.add_argument('-p', '--path', dest='path', metavar='PATH')
upload_parser.set_defaults(callback=commands.upload)

args = parser.parse_args()
args.callback(args)

