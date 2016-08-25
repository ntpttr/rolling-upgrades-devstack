# rolling-upgrades-devstack

This repo provides ansible playbooks to deploy devstack configured specifically for rolling upgrades testing across multiple nodes.
To deploy, first add the IPs of your target hosts to the inventory file, then run 
'ansible-playbook -i inventory playbooks/devstack_install.yml' to install the required packages and start up devstack on each node.

Once the cloud is up and running, the following process can be used to validate the rolling upgrades process:

1. On each node running any cinder service, check out the master branch in /opt/stack/cinder
2. On the control node, run 'cinder-manage db sync' to migrate the database to master.
3. Run the volume tempest tests ('tox -e all-plugin -- volume' from the tempest directory)
4. Restart the c-api service on the control node to upgrade it to master.
5. Repeat step 3
6. For each node running c-sch, restart c-sch on that node, repeating step 3 after each restart.
7. Repeat step 6 with c-vol.
8. Repeat step 6 with c-bak.

NOTE: Tempest will run and then clean everything up at the end, meaning that just these steps won't validate data consistency throughout
the upgrade process. For a complete test, I'm also working on scripts that will create a volume and a backup, attach the volume to a running
instance and validate that data on the volume stays consistent and reads/writes still work at every phase of the upgrade. Until those
are finished, this can be done manually. In that case, you could crate a volume, attach it to a VM, write some data to it and back it up
and after each service upgrades validate that all the data was maintained and reads and writes are still successful.
