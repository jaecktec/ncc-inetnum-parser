import os
import shutil
import tempfile
import threading
from datetime import datetime
from time import mktime
from unittest import TestCase, main
from uuid import uuid4

from . import update_ftp_file
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import hashlib


def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def file_content_to_string(fname):
    with open(fname, 'r') as file:
        return file.read().replace('\n', '')


def serve_fn(server):
    server.serve_forever()


class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target_asdf = target
        self._args_asdf = args
        threading.Thread.__init__(self)

    def run(self):
        self._target_asdf(*self._args_asdf)


class TestLambdaHandler(TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        s = str(tempfile.gettempdir()) + "/" + str(uuid4())
        os.mkdir(s)
        self.file_location = s
        self.cleanup_folders = [self.file_location]

    def setUp(self):
        copy_file_with_fixed_creation_date(self.file_location)
        authorizer = DummyAuthorizer()
        authorizer.add_anonymous(self.file_location)

        self.downloaded_files = []

        def record_file_sent(a, b):
            self.downloaded_files.append(b)

        handler = FTPHandler
        handler.on_file_sent = record_file_sent
        handler.authorizer = authorizer

        self.server = FTPServer(("localhost", 1026), handler)

        t1 = FuncThread(serve_fn, self.server)
        t1.start()
        pass

    def test_downloads_new_file(self):
        self.downloaded_files = []
        target_folder = str(tempfile.gettempdir()) + "/" + str(uuid4())
        os.mkdir(target_folder)
        self.cleanup_folders.append(target_folder)
        update_ftp_file.update_file(
            ftp_uri="ftp://localhost:1026/some.db",
            soruce_name="some.db",
            target_folder=target_folder)

        assert os.path.exists(target_folder + "/some.db")
        assert md5(target_folder + "/some.db") == "cec86c49621276b57de7ca1aecf1c84d"
        assert os.path.exists(target_folder + "/some.db.last_mod.txt")
        assert file_content_to_string(target_folder + "/some.db.last_mod.txt") == "2020-01-01-00-00-00"

    def test_not_download_existing_file(self):
        target_folder = str(tempfile.gettempdir()) + "/" + str(uuid4())
        os.mkdir(target_folder)
        self.cleanup_folders.append(target_folder)
        with open(target_folder + "/some.db", 'w') as handle:
            handle.write("I am content")
        with open(target_folder + "/some.db.last_mod.txt", 'w') as handle:
            handle.write("2020-01-01-00-00-00")
        update_ftp_file.update_file(
            ftp_uri="ftp://localhost:1026/some.db",
            soruce_name="some.db",
            target_folder=target_folder)

        assert len(self.downloaded_files) < 1
        assert os.path.exists(target_folder + "/some.db")
        assert file_content_to_string(target_folder + "/some.db") == "I am content"
        assert os.path.exists(target_folder + "/some.db.last_mod.txt")
        assert file_content_to_string(target_folder + "/some.db.last_mod.txt") == "2020-01-01-00-00-00"

    def tearDown(self) -> None:
        for folder in self.cleanup_folders:
            shutil.rmtree(folder)

        self.server.close_all()


def copy_file_with_fixed_creation_date(file_location):
    target_file = file_location + "/some.db"
    shutil.copyfile(os.path.dirname(os.path.realpath(__file__)) + '/../test_ftp_home/some.db',
                    target_file)
    date = datetime(year=2020, month=1, day=1, hour=1, minute=0, second=0)
    mod_time = mktime(date.timetuple())
    os.utime(path=target_file, times=(mod_time, mod_time))


def delete_s3_bucket(bucket_name, s3):
    s3_objects = s3.list_objects(Bucket=bucket_name)
    if 'Contents' in s3_objects:
        for key in s3_objects['Contents']:
            s3.delete_object(Bucket=bucket_name, Key=key['Key'])
    s3.delete_bucket(Bucket=bucket_name)


if __name__ == '__main__':
    main()
