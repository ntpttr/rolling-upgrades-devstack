#!/usr/bin/env python

import argparse
import sys
from time import sleep

from cinderclient import client as blockclient
from novaclient import client as computeclient

def create_vol(cinder):
    vol = cinder.volumes.create(name='test-vol', size=3)
    while vol.status != 'available':
        vol = cinder.volumes.get(vol.id)
        print("Creating volume...")
        sleep(1)
    return vol

def create_vm(nova):
    fl = nova.flavors.find(name='m1.small')
    net = nova.networks.find(human_id='private')
    nics = [{'net-id': net.id,
             'port-id': '',
             'tag': '',
             'v6-fixed-ip': '',
             'net-name': '',
             'v4-fixed-ip': ''}]
    image = nova.images.find(name='cirros-0.3.4-x86_64-uec')
    vm = nova.servers.create('test-vm', image, fl, nics=nics)
    while vm.status != 'ACTIVE':
        vm = nova.servers.get(vm.id)
        print("Spinning up vm...")
        sleep(1)
    return vm

def attach_volume(nova, cinder, vol, vm):
    nova.volumes.create_server_volume(vm.id, vol.id)
    while vol.status != 'in-use':
        vol = cinder.volumes.get(vol.id)
        print(vol.status)
        sleep(1)

def main(args):
    cinder = blockclient.Client('2', args.username, args.password, args.tenant, args.authurl)
    nova = computeclient.Client('2', args.username, args.password, args.tenant, args.authurl)

    vol = create_vol(cinder)
    vm = create_vm(nova)
    attach_volume(nova, cinder, vol, vm)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', metavar='STRING',
                        required=True, help="OpenStack user name")
    parser.add_argument('--password', metavar='STRING',
                        required=True, help="OpenStack password")
    parser.add_argument('--tenant', metavar='STRING',
                        required=True, help="OpenStack tenant name")
    parser.add_argument('--authurl', metavar='STRING',
                        required=True, help="OpenStack auth url")
    args = parser.parse_args()
    sys.exit(main(args))
