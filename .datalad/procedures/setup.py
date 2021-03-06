#!/usr/bin/env python3

import sys
import os
import re

import datalad.api
from datalad.distribution.dataset import require_dataset

import argparse

parser = argparse.ArgumentParser(description='setup the dataset siblings')
parser.add_argument('path', help = 'path')
parser.add_argument('--confidential', help = 'setup access to confidential data', action = 'store_true')
parser.add_argument('--private', help = 'setup access to private data', action = 'store_true')

args = parser.parse_args()

confidential = args.confidential or args.private
private = args.private

ds = require_dataset(
    sys.argv[1],
    check_installed = True,
    purpose = 'configure'
)

origin_url = datalad.api.siblings(name = 'origin', dataset = ds)[0]['url']
dataset_name = os.path.splitext(os.path.basename(origin_url))[0]
private_organization = 'LAAC-LSCP'
el1000_organization = 'EL1000'

el1000_url = "git@gin.g-node.org:/{}/{}.git".format(el1000_organization, dataset_name)
private_url = "git@gin.g-node.org:/{}/{}.git".format(private_organization, dataset_name)
confidential_url = "git@gin.g-node.org:/{}/{}-confidential.git".format(el1000_organization, dataset_name)

siblings = {
    'private': {'url': private_url, 'wanted': 'include=*' },
    'el1000': {'url': el1000_url, 'wanted': '(metadata=EL1000=*) and (exclude=**/confidential/*)'},
    'confidential': {'url': confidential_url, 'wanted': '(metadata=EL1000=*) and (include=**/confidential/*)'}
}

origin = None
for sibling in siblings.keys():
    if siblings[sibling]['url'] == origin_url:
        origin = sibling

if origin is None:
    raise Exception('failed to determine where this repository has been cloned from.')

if origin == 'confidential':
    raise Exception('please install the dataset from {}'.format(el1000_url))

args = parser.parse_args()

ds = require_dataset(
    args.path,
    check_installed = True,
    purpose = 'configuration'
)

for sibling in siblings.keys():
    name = 'origin' if sibling == origin else sibling

    if sibling == 'private' and not private:
        continue

    if sibling == 'confidential' and not confidential:
        continue

    datalad.api.siblings(
        name = name,
        dataset = ds,
        action = 'configure',
        url = siblings[sibling]['url']
    )

    datalad.api.siblings(
        name = name,
        dataset = ds,
        action = 'configure',
        annex_wanted = siblings[sibling]['wanted'],
        annex_required = siblings[sibling]['wanted']
    )

available_siblings = {sibling['name'] for sibling in datalad.api.siblings(dataset = ds)}

datalad.api.siblings(
    name = 'origin',
    dataset = ds,
    action = 'configure',
    publish_depends = (set(siblings.keys()) & available_siblings) - {'origin', origin}
)
