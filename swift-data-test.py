#!/usr/bin/env python

"""
Tiny program to repeateadly download a random object from a swift container
and compare its hash with what is listed in the container.

Author: Ganesh Mahalingam
"""

import argparse
from random import choice, randint
import sys
from hashlib import md5
from os import remove, path
from shutil import rmtree
from swiftclient.service import SwiftError, SwiftService
from tempfile import mkdtemp
from time import sleep


def obj_list(container):
    """
    Identify the list of objects in the given container
    Returns a dict of object_name and hash value
    """
    obj_list = {}

    try:
        with SwiftService() as swift:
            objs = swift.list(container=container)
            for entry in objs:
                if entry['success']:
                    for item in entry['listing']:
                        name = item['name']
                        obj_list[name] = item['hash']
                else:
                    raise entry['error']
            return obj_list
    except SwiftError as e:
        sys.exit(e.value)


def check_obj(container, objlist):
    """
    With the given object list and container name, download a random object and
    compare its hash value with listed value.
    """

    destdir = mkdtemp()
    downopts = {'out_directory': destdir}
    count = 0
    try:
        while True:
            sleep(randint(0, 10))
            with SwiftService() as swift:
                obj = choice(objlist.keys())
                for dobj in swift.download(container=container, objects=[obj],
                                           options=downopts):
                    if dobj['success']:
                        downfile = path.join(destdir, obj)
                        hashval = md5(open(downfile, 'rb').read()).hexdigest()
                        if objlist[obj] != hashval:
                            print "Downloaded file %s does not match its"
                            "md5sum. Value was %s but"
                            "expected %s" % (obj, hashval, objlist[obj])
                            raise
                        count += 1
                        print "Count: %d. File tested: %s" % (count, obj)
                        remove(downfile)
                    else:
                        raise dobj['error']
    except SwiftError as e:
        rmtree(destdir)
        sys.exit(e.value)
    except:
        rmtree(destdir)
        sys.exit()


def main(args):
    list = obj_list(args.container)
    check_obj(args.container, list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--container', metavar='STRING',
                        required=True,
                        help="Container you wish to run the test on")

    args = parser.parse_args()
    sys.exit(main(args))
