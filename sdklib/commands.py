import os
import os.path as path
import shutil
import stat
import sys

from flask import Flask, request, url_for, send_from_directory
from jinja2 import Environment, FileSystemLoader
import yaml

from sdklib import logger, skeleton_path


def create(args):
    location = path.abspath(args.path)
    if path.exists(location):
        logger.error('Directory %s already exists' % location)
        sys.exit(1)

    logger.info('Creating project')
    if args.bootstrap:
        paths = (
            ('',),
            ('data',)
        )
    else:
        paths = (
            ('',),
            ('static',),
            ('static', 'img'),
            ('static', 'css'),
            ('static', 'js'),
            ('templates',),
            ('data',)
        )
    for p in paths:
        new_path = path.join(location, *p)
        logger.info('Creating directory %s' % new_path)
        os.mkdir(new_path)

    if args.bootstrap:
        logger.info('Copying Twitter Bootstrap framework files')
        paths_copy = ('static', 'templates')
        for p in paths_copy:
            new_path = path.join(location, p)
            bootstrap_path = path.join(skeleton_path, 'bootstrap', p)
            shutil.copytree(bootstrap_path, new_path)

    yaml_src = path.join(skeleton_path, 'app.yaml')
    yaml_dest = path.join(location, 'app.yaml')
    logger.info('Creating blank project file %s' % yaml_dest)
    shutil.copy(yaml_src, yaml_dest)
    os.chmod(yaml_dest, stat.S_IWUSR | stat.S_IRUSR)


def run_server(args):
    app_path = path.abspath(args.path)
    yaml_path = path.join(app_path, 'app.yaml')
    templates_path = path.join(app_path, 'templates')
    static_path = path.join(app_path, 'static')
    try:
        logger.info('Loading %s' % yaml_path)
        config = yaml.load(open(yaml_path, 'r').read())
    except IOError:
        logger.error('Error reading %s' % yaml_path)
        sys.exit(2)

    if 'routes' not in config:
        logger.error('Routes not specified in app.yaml')
        sys.exit(3)

    jinja_env = Environment(
        loader=FileSystemLoader(templates_path),
        extensions=['pyjade.ext.jinja.PyJadeExtension']
    )
    def _dispatch_rule(**kwargs):
        for k, v in kwargs.iteritems():
            if isinstance(v, unicode):
                kwargs[k] = str(v)
        template = jinja_env.get_template(kwargs['__sdk_template__'])
        data = _compile_defaults(kwargs['__sdk_data__'], app_path)
        for k in data:
            kwargs.setdefault(k, data[k])
        kwargs['REQ'] = request
        kwargs['GET'] = request.args
        kwargs['POST'] = request.form
        kwargs['COOKIES'] = request.cookies
        return template.render(**kwargs)

    def _dispatch_static(filename):
        return send_from_directory(static_path, filename)

    def _compile_defaults(files, app_path):
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
                logger.error('Error reading data file %s' % file_path)
            data.update(file_data)    
        return data

    app = Flask(__name__)
    i = 0
    for route in config['routes']:
        rule = route['rule']
        endpoint = 'dispatch_%s' % str(i)
        defaults = {}
        defaults['__sdk_template__'] = route['template']
        defaults['__sdk_data__'] = route.get('data', [])
        app.add_url_rule(
            rule,
            endpoint,
            _dispatch_rule,
            defaults=defaults
        )
        i += 1
    app.add_url_rule('/static/<path:filename>', 'static', _dispatch_static)

    host = ''.join(args.address.split(':')[:-1])
    port = int(args.address.split(':')[-1])
    app.run(host=host, port=port, debug=True)



