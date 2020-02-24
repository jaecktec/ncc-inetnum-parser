#! /bin/bash

root=$(pwd)

rm -rf build

pip3 install -r ./requirements.txt --target ./build --upgrade
cp src/update_ftp_file.py build

cd build
zip -r ../out.zip . -x *.pyc
