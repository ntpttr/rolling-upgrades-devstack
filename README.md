# rolling-upgrades-devstack

This repo provides ansible playbooks to deploy devstack configured specifically for rolling upgrades testing across multiple nodes.
To deploy, first add the IPs of your target hosts to the inventory file, then run 
'ansible-playbook -i inventory playbooks/devstack_install.yml' to install the required packages and start up devstack on each node.

Before performing the rolling upgrade, some setup is required for validating data consistency of volumes and backups, as well as testing read/write during the upgrade.

To set up a volume, attach it to an instance, write to it, and back it up, run 'python setup-storage.py'. This script will expect you to pass in arguments for authentication, including user name, password, tenant name and auth url.

After this script finishes, start up the two validation scripts (in seperate tmux or screen sessions). These will be left running for the duration of the upgrade, and will test reads/writes to the volume as well as the consistency of the backup.

Once the cloud is up and running and the setup scripts have been run, the following process can be used to validate the rolling upgrades process:

1. On each node running any cinder service, check out the master branch in /opt/stack/cinder
2. On the control node, run 'cinder-manage db sync' to migrate the database to master.
3. Run the volume tempest tests ('tox -e all-plugin -- volume' from the tempest directory)
4. Restart the c-api service on the control node to upgrade it to master.
5. Repeat step 3
6. For each node running c-sch, restart c-sch on that node, repeating step 3 after each restart.
7. Repeat step 6 with c-vol.
8. Repeat step 6 with c-bak.
