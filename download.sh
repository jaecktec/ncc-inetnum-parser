#!/bin/sh
mkdir -p downloads
wget -O downloads/arin.db.gz  ftp://ftp.arin.net/pub/rr/arin.db.gz
wget -O downloads/larnic.db   ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-extended-latest
wget -O downloads/apnic-v6.gz ftp://ftp.apnic.net/pub/apnic/whois/apnic.db.inet6num.gz
wget -O downloads/apnic-v4.gz ftp://ftp.apnic.net/pub/apnic/whois/apnic.db.inetnum.gz
wget -O downloads/afrinic.gz  ftp://ftp.afrinic.net/pub/dbase/afrinic.db.gz
wget -O downloads/ripe-v4.gz  ftp://ftp.ripe.net/ripe/dbase/split/ripe.db.inetnum.gz
wget -O downloads/ripe-v6.gz  ftp://ftp.ripe.net/ripe/dbase/split/ripe.db.inet6num.gz