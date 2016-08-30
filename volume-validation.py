import argparse
import paramiko
from random import randint
import sys
from time import sleep

def check_data(ssh):
    count = 0
    stdin, stdout, stderr = ssh.exec_command("sudo md5sum /data/test.txt")
    prev_hash = stdout.readlines()
    try:
        while True:
            sleep(randint(0, 10))

            # Test read from volume
            stdin, stdout, stderr = ssh.exec_command("sudo md5sum /data/test.txt")
            new_hash = stdout.readlines()
            if prev_hash != new_hash:
                print("Data on volume has been corrupted. md5sum was %s but "
                      "expected %s" % (new_hash, prev_hash))
                raise
            print("Read successful. Data intact.")

            # Test write to volume
            stdin, stdout, stderr = ssh.exec_command("sudo dd if=/dev/zero of=/data/test_write.txt, bs=1M count=10")
            if stderr.readlines() == [u'10+0 records in\n', u'10+0 records out\n']:
                print("Write successful.")
            else:
                print("Failed to write to volume.")
                raise

            count += 1
            print("Count: %d" % (count))
    except:
        print("Exiting")
        sys.exit()

def main(args):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy())
    ssh.connect(args.ip, username='cirros', password='cubswin:)')

    check_data(ssh)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', metavar='STRING',
                        required=True, help="Nova instance IP address")
    args = parser.parse_args()
    sys.exit(main(args))
