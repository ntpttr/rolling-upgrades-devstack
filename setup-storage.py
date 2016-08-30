#!/usr/bin/env python

import argparse
import paramiko
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
    nova.volumes.create_server_volume(vm.id, vol.id)
    while vol.status != 'in-use':
        vol = cinder.volumes.get(vol.id)
        print("Attaching volume...")
        sleep(1)
    vm = nova.servers.get(vm.id)
    return vm, vol

def assign_vm_ip(neutron, nova, vm):
    networks = neutron.list_networks(name='public')
    network_id = networks['networks'][0]['id']
    body = { 'floatingip': { 'floating_network_id': network_id, 'port_id': vm.interface_list()[0].port_id } }
    vm_addresses = vm.addresses
    ip = neutron.create_floatingip(body=body)['floatingip']['floating_ip_address']
    while vm.addresses == vm_addresses:
        vm = nova.servers.get(vm.id)
        print("Creating floating IP...")
        sleep(3)
    return vm, ip

def set_up_device(ssh):
    print("Formatting device...")
    ssh.exec_command("(echo o; echo n; echo p; echo 1; echo ; echo ; echo w) | sudo /sbin/fdisk /dev/vdb")
    sleep(0.5)
    ssh.exec_command("sudo /usr/sbin/mkfs.ext4 /dev/vdb1")
    sleep(0.5)
    ssh.exec_command("sudo mkdir /data")
    sleep(0.5)
    ssh.exec_command("sudo mount /dev/vdb1 /data")
    sleep(0.5)
    ssh.exec_command("sudo dd if=/dev/zero of=/data/test.txt bs=1M count=100")

def backup_volume(cinder, vol_id):
    bak = cinder.backups.create(vol_id, name='test-bak', force=True)
    while bak.status != 'available':
        bak = cinder.backups.get(bak.id)
        print("Backing up volume...")
        sleep(5)

def main(args):
    auth = v2.Password(auth_url=args.authurl, username=args.username, password=args.password, tenant_name=args.tenant)
    sess = session.Session(auth=auth)
    cinder = blockclient.Client('2', args.username, args.password, args.tenant, args.authurl)
    nova = computeclient.Client('2', args.username, args.password, args.tenant, args.authurl)
    neutron = networkclient.Client(session=sess)

    vol = create_vol(cinder)
    vm = create_vm(nova)
    vm, vol = attach_volume(nova, cinder, vol, vm)
    vm, ip = assign_vm_ip(neutron, nova, vm)

    sleep(10)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy())
    ssh.connect(ip, username='cirros',  password='cubswin:)')

    set_up_device(ssh)

    backup_volume(cinder, vol.id)

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
