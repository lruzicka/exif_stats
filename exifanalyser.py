#!/usr/bin/python3
"""
The Exif Analyser, version 0.9


Created by Lukas Ruzicka (lruzicka@redhat.com) under the GPLv3 license
"""

import argparse
import exifread
import json
import os
from collections import Counter
from termcolor import colored

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

    def return_args(self):
        """Return arguments used on CLI"""
        args = self.parser.parse_args()
        return args

class FileTree:
    """ Holds info and methods operating on a file tree. """
    def __init__(self, workdir, suffix):
        """ Initializes the File tree and creates a list of all json file paths. """
        self.leaves = []
        temporary = []
        for root, dirs, files in os.walk(workdir):
            for f in files:
                path = os.path.join(root, f)
                temporary.append(path)
        for leaf in temporary:
            if suffix.lower() in leaf[-3:].lower():
                self.leaves.append(leaf)

    def count(self):
        """ Return the number of files. """
        return len(self.leaves)

    def return_paths(self):
        """Return all found paths."""
        return self.leaves

class FileReader:
    """ Holds info and methods for file parsing. """
    def __init__(self, path):
        """ Initializes the class with all possible paths. """
        self.path = path
        
    def read_tags(self):
        imagefile = open(self.path, 'rb')
        tags = exifread.process_file(imagefile, details=False)
        imagefile.close()
        return tags

class FileAnalyser:
    """Calculates stats for a given EXIF tag."""
    def __init__(self, batch):
        self.batch = batch
        self.calculations = {}
        self.total = 0

    def return_stats(self, tag):
        values = []
        for image in self.batch:
            reader = FileReader(image)
            tags = reader.read_tags()
            try:
                value = tags[tag]
            except KeyError:
                pass
            values.append(str(value))
        self.calculations = Counter(values)
        self.total = len(values)
        return self.calculations

    def humanify_stats(self):
        result = []
        keys = self.calculations.keys()
        keys = list(keys)
        for key in keys:
            value = self.calculations[key]
            percentage = round((value/self.total)*100, 0)
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

    if command == 'show':
        if not imagefile:
            print("No file name has been given. Please, enter a file to read from.")
        else:
            reader = FileReader(imagefile)
            tags = reader.read_tags()
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
        result = analyse.humanify_stats()
        for line in result:
            print(f"{line[1]} \t| {line[0]} %")

    elif command == 'search':
        pass

    else:
        print('Nothing to do.')

    #exifTree = FileTree(workdir, suffix)
    #images = exifTree.return_paths()
    #print(exifTree.count())
    #for image in images:
    #    print(image)




if __name__ == '__main__':
    main()
