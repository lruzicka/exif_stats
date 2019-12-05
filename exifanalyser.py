#!/usr/bin/python3
"""
The Exif Analyser, version 0.9


Created by Lukas Ruzicka (lruzicka@redhat.com) under the GPLv3 license
"""

import argparse
import json
import os
import re
import subprocess
from collections import Counter

class Parser:
    """This holds the argument parsing tool."""
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.subparser = self.parser.add_subparsers(dest='command')
        self.searchparse = self.subparser.add_parser('search')
        self.searchparse.add_argument('-t', '--tags', default=None,
                help='Comma separated list of exif tags to search in files')
        self.searchparse.add_argument('-s', '--suffix', default='dng',
                help='Comma separated list of file suffixes to search in')
        self.searchparse.add_argument('-w', '--workdir', default='.', help='The directory where the search should be started.')
        self.statparse = self.subparser.add_parser('stats')
        self.statparse.add_argument('-t', '--tag', default='EXIF ISOSpeedRatings', help='The Exif tag for which the stats should be calculated.')
        self.statparse.add_argument('-s', '--suffix', default='dng',
                help='Comma separated list of file suffixes to search in')
        self.statparse.add_argument('-w', '--workdir', default='.', help='The directory where the search should be started.')
        self.showparse = self.subparser.add_parser('show')
        self.showparse.add_argument('-f', '--file', default=None, help='Show EXIF information for a given file.')
        self.showparse.add_argument('-t','--tag', default=None, help='Tag to show options for.')

    def return_args(self):
        """Return arguments used on CLI"""
        args = self.parser.parse_args()
        return args

class FileReader:
    """ Holds info and methods for file parsing. """
    def __init__(self, path, params=None):
        """ Initializes the class with all possible paths. """
        self.path = path
        self.params = params
        
    def read_tags(self):
        """ Reads EXIF tags from the files in the directory tree. """
        tags = {}
        database = {}
        params = ['exiftool']
        if self.params:
            params = params + self.params
        params.append(self.path)
        try:
            run = subprocess.run(params, capture_output=True)
            exifdata = run.stdout.decode('utf8').split('\n')

            match = re.match('=+', exifdata[0])
            if not match: # Then it is not a multi exif
                for line in exifdata:    
                   try:
                       rec = line.split(':')
                       key = rec[0].strip()
                       value = rec[1].strip()
                       tags[key] = value
                   except IndexError:
                       pass
                database[self.path] = tags
            else:
                path = 'unknown'
                for line in exifdata:
                    match = re.match("=+", line)
                    if match:
                        path = line.split(' ')[1].strip()
                        database[path] = []
                    else:
                        database[path] = database[path]+[line] 
                for path in database.keys():
                    exif = database[path]
                    tags = {}
                    for tag in exif:
                        try:
                            rec = tag.split(':')
                            key = rec[0].strip()
                            value = rec[1].strip()
                            tags[key] = value
                        except IndexError:
                            pass
                    database[path] = tags

        except FileNotFoundError:  
            print('This program cannot work without EXIFTOOL. Please, install it first.')
            print('If you are on Fedora, use `sudo dnf install perl-Image-ExifTool`')
            print('====================================================================')
            print('Good bye!')
        self.database = database
        return database 

    def get_file_data(self, filename):
        return self.database[filename]

class FileAnalyser:
    """Calculates stats for a given EXIF tag."""
    def __init__(self, database):
        self.dbase = database
        self.calculations = {}
        self.total = len(self.dbase.keys()) 

#    def show_file_exif(self, image):
#        return self.dbase[image]

    def return_stats(self, tag):
        """ Return raw sums for found EXIF tags. """
        values = []
        for image in self.dbase.keys():
            tags = self.dbase[image]
            try:
                value = tags[tag]
            except KeyError:
                value = 'not available'
            values.append(value)
        self.calculations = Counter(values)
        self.total = len(values)
        return self.calculations

    def process_stats(self):
        """ Calculate percentages and sort results. """
        result = []
        keys = self.calculations.keys()
        keys = list(keys)
        for key in keys:
            value = self.calculations[key]
            percentage = round((value/self.total)*100, 2)
            result.append((percentage, key, value))
        result.sort(reverse=True)
        return result

class Outputter:
    """ Formats output for console. """
    def __init__(self, level=1):
        self.linelen = 50
        self.level = level
        self.textlen = 0
        self.symbols = {0:'=', 1:'-', 2:'.', 3:'#', 4:'!'}

    def textout(self, text):
        self.textlen = len(text) + 4
        toprint = []
        symbol = self.symbols[self.level]
        decor = self.textlen * symbol
        line = f"{symbol} {text} {symbol}"
        if self.level < 2:
            toprint.append(decor)
            line = f"{symbol} {text} {symbol}"
            toprint.append(line)
            toprint.append(decor)
        else:
            line = f" >> {text}"
            toprint.append(line)
        toprint.append(' ')
        for line in toprint:
            print(line)

    def tableout(self, data):
        """ Make a table out of data, accepts the dictionary of keys: values. """
        longest = 0
        for key in data.keys():
            if len(key) > longest:
                longest = len(key)
        tabfill = 1
        for key in data.keys():
            tabfill = (longest-len(key))+1
            tab = tabfill * ' '
            print(f"{key}{tab}: {data[key]}")
                
    def graph(self, data):
        """ Make a graph out of statistics data, accepts lists with tuples (perc, keys, count) """
        longest = 0
        for item in data:
            if len(item[1]) > longest:
                longest = len(item[1])
        tabfill = 1
        for item in data:
            tabfill = (longest-len(item[1]))+1
            tab = tabfill * ' '
            barlen = int((item[0]/100)*50)
            bar = barlen * self.symbols['bar']
            print(f"{item[1]}{tab}: {bar} {int(item[0])}% ({item[2]} files)")

def main():
    """ Main program """
    # Register printers
    h1 = Outputter(0)
    h2 = Outputter(1)
    h3 = Outputter(2)
    bar = Outputter(3)
    warn = Outputter(4)

    h1.textout('Exif Analyser 0.9:')
    
    # Collect CLI arguments
    argparser = Parser()
    args = argparser.return_args()

    command = args.command
    if command == 'search':
        tag = args.tags
        workdir = args.workdir
        suffix = args.suffix
    elif command == 'stats':
        tag = args.tag
        workdir = args.workdir
        suffix = args.suffix
    else:
        try:
            imagefile = args.file
            tag = args.tag
        except AttributeError:
            warn.textout("You should add some parameters. Try the -h switch.")

    if command == 'show':
        reader = FileReader(imagefile)
        reader.read_tags()
        tags = reader.get_file_data(imagefile)
        bar.tableout(tags)

    elif command == 'stats':
        if suffix:
            params = ['-ext', suffix, '-r.']
        reader = FileReader(workdir, params)
        h3.textout("Waiting for the ExifTool backend to finish. This can take some time.")
        dbase = reader.read_tags()
        totaltags = len(dbase.keys())
        h3.textout(f"{totaltags} files have been found in `{workdir}`.")
        analyse = FileAnalyser(dbase)
        result = analyse.return_stats(tag)
        h3.textout(f"Calculating statistics based on these files.")
        h2.textout(f"Frequency statistics for the '{tag}' tag:")
        result = analyse.process_stats()
        bar.graph(result)

    elif command == 'search':
        print("This function has not been implemented yet.")

    else:
        print('Nothing to do.')

if __name__ == '__main__':
    main()
