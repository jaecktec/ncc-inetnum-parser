import tempfile
from datetime import datetime

import boto3
import os
from ftplib import FTP
from urllib.parse import urlparse

from botocore.exceptions import ClientError


def lambda_handler(event, context):
    s3_client = None
    if os.getenv("AWS_S3_ENDPOINT_URL") is None:
        s3_client = boto3.client('s3')
    else:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
            endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL")
        )
    ftp_uri = event["source_ftp_uri"]
    soruce_name = event["source_name"]
    bucket_name = event["bucket_name"]
    o = urlparse(ftp_uri)
    ftp = FTP()
    if o.port is None:
        ftp.connect(host=o.hostname)
    else:
        ftp.connect(host=o.hostname, port=o.port)
    ftp.login()
    path_split = o.path.split('/')
    for path_elem in path_split[:(len(path_split) - 1)]:
        if path_elem is '':
            continue
        ftp.cwd(path_elem)
        pass

    s3_filename = compute_filename(ftp, o, soruce_name)
    if does_resource_exist(s3_client, bucket_name, s3_filename):
        return
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
    with open(temp.name, 'wb') as handle:
        ftp.retrbinary('RETR %s' % path_split[-1], handle.write)
    s3_client.upload_file(temp.name, bucket_name, s3_filename)
    os.remove(temp.name)


def does_resource_exist(s3_client, bucket_name, resource_name) -> bool:
    try:
        head = s3_client.head_object(Bucket=bucket_name, Key=resource_name)
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise
    return True


def compute_filename(ftp, o, soruce_name) -> str:
    timestamp_str = ftp.voidcmd("MDTM %s" % o.path)[4:].strip()  # '20200101000000' -> '2020 01 01 00 00 00'
    timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
    s3_filename = '{}-{}'.format(timestamp.strftime("%Y-%m-%d-%H-%M-%S"), soruce_name)
    return s3_filename
