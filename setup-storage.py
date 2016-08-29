#!/usr/bin/env python

import argparse
import sys
from time import sleep

from cinderclient import client as blockclient
from keystoneauth1.identity import v2
from keystoneauth1 import session
from neutronclient.v2_0 import client as networkclient
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
    nova.volumes.create_server_volume(vm.id, vol.id, device='/dev/vdz')
    while vol.status != 'in-use':
        vol = cinder.volumes.get(vol.id)
        print("Attaching volume...")
        sleep(1)

def assign_vm_ip(neutron, vm):
    networks = neutron.list_networks(name='public')
    network_id = networks['networks'][0]['id']
    body = { 'floatingip': { 'floating_network_id': network_id, 'port_id': vm.interface_list()[0].port_id } }
    ip = neutron.create_floatingip(body=body)

def main(args):
    auth = v2.Password(auth_url=args.authurl, username=args.username, password=args.password, tenant_name=args.tenant)
    sess = session.Session(auth=auth)
    cinder = blockclient.Client('2', args.username, args.password, args.tenant, args.authurl)
    nova = computeclient.Client('2', args.username, args.password, args.tenant, args.authurl)
    neutron = networkclient.Client(session=sess)

    vol = create_vol(cinder)
    vm = create_vm(nova)
    attach_volume(nova, cinder, vol, vm)
    assign_vm_ip(neutron, vm)

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
    parser.add_argument('--neutronendpoint', metavar='STRING',
                        required=True, help="Neutron endpoint")
    args = parser.parse_args()
    sys.exit(main(args))

