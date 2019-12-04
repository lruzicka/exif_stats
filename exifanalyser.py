#!/usr/bin/python3
"""
The Exif Analyser, version 0.9


Created by Lukas Ruzicka (lruzicka@redhat.com) under the GPLv3 license
"""

import argparse
import exifread
import json
import os
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
            if '===' not in exifdata[0]:
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
                for line in exifdata:
                    if line[:4] == '===':
                        filepath = line.split(' ')[1].strip()
                    else:    
                        try:
                            rec = line.split(':')
                            key = rec[0].strip()
                            value = rec[1].strip()
                        except IndexError:
                            pass
                        tags[key] = value
                    database[filepath] = tags

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

    def return_stats(self, tag):
        """ Return raw sums for found EXIF tags. """
        values = []
        for image in self.dbase.keys():
            tags = self.dbase.get_file_data(image)
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
            result.append((percentage, key))
        result.sort(reverse=True)
        return result
            
def main():
    """ Main program """
    print('Exif Analyser:')
    print('==================================================')
    
    # Collect CLI arguments
    argparser = Parser()
    args = argparser.return_args()

    command = args.command
    if command == 'search':
        tag = args.tags
        workdir = args.workdir
        suffix = args.suffix.lower()
    elif command == 'stats':
        tag = args.tag
        workdir = args.workdir
        suffix = args.suffix.lower()
    else:
        imagefile = args.file
        tag = args.tag

    if command == 'show':
        reader = FileReader(imagefile)
        reader.read_tags()
        tags = reader.get_file_data(imagefile)
        for tag in tags.keys():
            print(tag, ' : ', tags[tag])

    elif command == 'stats':
        fileTree = FileTree(workdir, suffix)
        images = fileTree.return_paths()
        analyse = FileAnalyser(images)
        result = analyse.return_stats(tag)
        print(f"Calculating stats from {fileTree.count()} image files.")
        print("-------------------------------------------------------")
        print(f"Frequency statistics for '{tag}': \n")
        result = analyse.process_stats()
        for line in result:
            print(f"{line[1]} \t| {line[0]} %")

    elif command == 'search':
        print("This function has not been implemented yet.")

    else:
        print('Nothing to do.')

if __name__ == '__main__':
    main()
