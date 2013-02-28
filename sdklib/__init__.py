import logging
import os.path
import sys


path_name = os.path.dirname(sys.argv[0])
root_path = os.path.abspath(path_name)
skeleton_path = os.path.join(root_path, 'skeletons')

conlog = logging.StreamHandler()
logger = logging.getLogger('console')
logger.addHandler(conlog)
logger.setLevel(logging.INFO)

