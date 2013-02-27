import argparse 
import json
import os
import os.path as path
import sqlite3
import stat
import sys
import yaml

from flask import Flask, request
from jinja2 import Environment, FileSystemLoader


app_yaml = '''# Application Configuration File

# not used yet
api_access_key:
api_secret_key:

####################
# Routing
####################
# Routes are an array of mappings. The bare minimum of each mapping are the
# "rule" and "script" keys. An optional "data" key should point to the 
# file of the yaml or json data file in the data/ directory. If an array of
# files are given, it will load in sequence and each succeeding file will 
# override any existing keys. You can mix data formats.

#routes:
#  - rule: /
#    script: home.jade
#  - rule: /about-us/
#    script: about-us.jade
#    data: team.yaml
#  - rule: /portfolio/
#    script: portfolio.jade
#    data: [projects.json, clients.yaml]
'''


def cmd_create(args):
    location = path.abspath(args.path)
    sqlite_location = path.join(location, '.cms.db')
    yaml_location = path.join(location, 'app.yaml')
    if path.exists(location):
        print 'Directory %s already exists' % location
        sys.exit(1)

    print 'Creating project'
    paths = (
        ('',),
        ('static',),
        ('static', 'img'),
        ('static', 'css'),
        ('static', 'js'),
        ('scripts',),
        ('data',)
    )
    for p in paths:
        new_path = path.join(location, *p)
        print 'Creating directory %s' % new_path
        os.mkdir(new_path)

    print 'Creating blank project file %s' % yaml_location
    with open(yaml_location, 'w') as app:
        app.write(app_yaml)
    os.chmod(yaml_location, stat.S_IWUSR | stat.S_IRUSR)


def cmd_run_server(args):
    app_path = path.abspath(args.path)
    yaml_path = path.join(app_path, 'app.yaml')
    scripts_path = path.join(app_path, 'scripts')
    try:
        print 'Loading %s' % yaml_path
        config = yaml.load(open(yaml_path, 'r').read())
    except IOError:
        print 'Error reading %s' % yaml_path
        sys.exit(2)

    jinja_env = Environment(
        loader=FileSystemLoader(scripts_path),
        extensions=['pyjade.ext.jinja.PyJadeExtension']
    )
    def dispatch(**kwargs):
        template = jinja_env.get_template(kwargs['_sdk_template_'])
        return template.render(**kwargs)

    app = Flask(__name__)
    i = 0
    for route in config['routes']:
        rule = route['rule']
        endpoint = 'dispatch_%s' % str(i)
        defaults = compile_defaults(route.get('data', []), app_path)
        defaults['_sdk_template_'] = route['script']
        app.add_url_rule(
            rule,
            endpoint,
            dispatch,
            defaults=defaults
        )
        i += 1

    host = ''.join(args.address.split(':')[:-1])
    port = int(args.address.split(':')[-1])
    app.run(host=host, port=port, debug=True)


def compile_defaults(files, app_path):
    if not isinstance(files, list):
        files = [files]
    data = {}
    for f in files:
        try:
            file_path = path.join(app_path, 'data', f)
            file_type = file_path.split('.')[-1]
            file_data = {}
            with open(file_path, 'r') as fh:
                if file_type == 'json':
                    file_data = json.load(fh)
                elif file_type == 'yaml':
                    file_data = yaml.load(fh.read())
        except:
            print 'Error reading data file %s' % file_path
            print sys.exc_info()[0]
        data.update(file_data)    
    return data


parser = argparse.ArgumentParser(description='SDK')
sub_parsers = parser.add_subparsers(help='Sub commands for the manager script')

create_parser = sub_parsers.add_parser('create', help='Create a new project at specified directory')
create_parser.add_argument('-p', '--path', dest='path', metavar='PATH')
create_parser.set_defaults(callback=cmd_create)

server_parser = sub_parsers.add_parser('run_server', help='Run server')
server_parser.add_argument(
    '-a', '--address', dest='address', metavar='ADDRESS', default='127.0.0.1:9000'
)
server_parser.add_argument(
    '-p', '--path', dest='path', metavar='PATH', default='.'
)
server_parser.set_defaults(callback=cmd_run_server)

args = parser.parse_args()
args.callback(args)

