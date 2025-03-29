from scrapy.cmdline import execute
import sys
import os

dirpath = os.path.dirname(os.path.abspath(__file__))
print(os.path.abspath(__file__))
sys.path.append(dirpath)

os.chdir(dirpath)
execute(['scrapy', 'crawl', 'learncpp'])