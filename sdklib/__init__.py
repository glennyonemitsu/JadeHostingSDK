import logging


conlog = logging.StreamHandler()
logger = logging.getLogger('console')
logger.addHandler(conlog)
logger.setLevel(logging.INFO)

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
