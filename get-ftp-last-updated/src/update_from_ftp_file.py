import os
from datetime import datetime

from ftplib import FTP
from urllib.parse import urlparse
from argparse import ArgumentParser


def update_ftp_file(ftp_uri, soruce_name, target_folder):
    o = urlparse(ftp_uri)
    ftp = FTP()
    if o.port is None:
        ftp.connect(host=o.hostname)
    else:
        ftp.connect(host=o.hostname, port=o.port)
    ftp.login()
    path_split = o.path.split('/')
    for path_elem in path_split[:(len(path_split) - 1)]:
        if path_elem == '':
            continue
        ftp.cwd(path_elem)
        pass

    dest_file = "{}/{}".format(target_folder, soruce_name)
    dest_file_timestamp = "{}/{}.last_mod.txt".format(target_folder, soruce_name)
    modification_date = get_modification_date(ftp, o)

    if does_resource_exist(dest_file_timestamp, modification_date):
        print("already have this file")
        return
    with open(dest_file_timestamp, 'w') as handle:
        handle.write(modification_date)


def does_resource_exist(resource_name, modification_date) -> bool:
    if not os.path.exists(resource_name):
        return False
    with open(resource_name, 'r') as file:
        return file.read() == modification_date


def get_modification_date(ftp, o) -> str:
    timestamp_str = ftp.voidcmd("MDTM %s" % o.path)[4:].strip()
    timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
    s3_filename = '{}'.format(timestamp.strftime("%Y-%m-%d-%H-%M-%S"))
    return s3_filename


if __name__ == '__main__':
    parser = ArgumentParser("download last modification timestamp of file")
    parser.add_argument('--source',
                        type=str,
                        required=True,
                        help='ftp uri of source')
    parser.add_argument('--name',
                        type=str,
                        required=True,
                        help='name of the source')
    parser.add_argument('--target',
                        type=str,
                        required=True,
                        help='where to store the file')

    args = parser.parse_args()
    print(args.name)
    update_ftp_file(ftp_uri=args.source, soruce_name=args.name, target_folder=args.target)
