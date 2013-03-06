import base64
from collections import OrderedDict
from datetime import datetime
import hashlib
import hmac
import json
import os
import os.path as path
import shutil
import stat
import StringIO
import sys
import urllib
import urllib2

from flask import Flask, request, url_for, send_from_directory
from jinja2 import Environment, FileSystemLoader
import requests
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


def upload(args):
    app_path = path.abspath(args.path)
    yaml_path = path.join(app_path, 'app.yaml')
    templates_path = path.join(app_path, 'templates')
    data_path = path.join(app_path, 'data')
    static_path = path.join(app_path, 'static')
    
    yaml_data = yaml.load(open(yaml_path, 'r').read())
    if 'api_access_key' not in yaml_data or \
       'api_secret_key' not in yaml_data:
        logger.error('app.yaml does not have data for keys "api_access_key" and "api_secret_key"')
        sys.exit(3)
        
    payload = {}
    cut_start = len(app_path) + 1
    for dirname, subdirs, files in os.walk(app_path):
        dn = dirname[cut_start:]
        if dn.startswith('templates') or \
           dn.startswith('data') or \
           dn.startswith('static'):
            for filename in files:
                filepath = path.join(dn, filename)
                fullfilepath = path.join(dirname, filename)
                payload[filepath] = _file_data(fullfilepath)

    payload_json = json.dumps(payload)
    hmac_obj = hmac.new(yaml_data['api_secret_key'], payload_json)
    app_data = {}
    app_data['payload_version'] = 1
    app_data['payload'] = payload_json
    app_data['api_access_key'] = yaml_data['api_access_key']
    app_data['signature'] = hmac_obj.hexdigest()
    app_json = json.dumps(app_data)

    try:
        form = _get_upload_form(
            yaml_data['api_access_key'], yaml_data['api_secret_key']
        )
        logger.info('Uploading')
        _upload_file(form, app_json)
        logger.info('Upload complete')
    except urllib2.HTTPError, e:
        #if e.code == 404:
        logger.error('API call returned a 404. Please check api '
                     'credentials in the app.yaml file.')


def _file_data(filename):
    with open(filename, 'r') as fh:
        data = fh.read()
        data64 = base64.b64encode(data)
        return data64

def _api_signature(verb, content, date, uri, secret):
    msg = '\n'.join([verb, content, date, uri])
    signer = hmac.new(secret, msg, hashlib.sha1)
    signature = signer.digest()
    signature64 = base64.b64encode(signature)
    return signature64

def _date_header():
    '''
    returns date string formatted to RFC1123 specified here in the first
    format shown.
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.3.1
    '''
    dt = datetime.utcnow()
    header = dt.strftime('%a, %d %b %y %H:%M:%S GMT')
    return header

def _get_upload_form(access_key, secret_key):
    api_verb = 'GET'
    api_content = ''
    api_date = _date_header()
    api_uri = '/api/get-upload-fields/'
    api_signature = _api_signature(
        api_verb, api_content, api_date, api_uri, secret_key
    )
    api_uri_full = 'http://glenn.platters.com:8090%s' % api_uri
    authn_name = 'X-Authentication'
    authn_value = 'PLATTERS %s:%s' % (access_key, api_signature)
    req = urllib2.Request(api_uri_full)
    req.add_header(authn_name, authn_value)
    req.add_header('Date', api_date)
    rsp = urllib2.urlopen(req)
    content = rsp.read()
    data = json.loads(content)
    return data

def _upload_file(form, file_data):
    data = { f['name']: f['value'] for f in form['fields'] }
    file_data_handler = StringIO.StringIO(file_data)
    res = requests.post(
        form['action'], 
        data=data, 
        files={'file': ('0', file_data_handler)}
    )
    return res
