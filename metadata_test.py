from importlib.metadata import version
from importlib import metadata

f = open("my_req.txt", 'r')

metadata(f)