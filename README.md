# ncc-inetnum-parser

This solution helps to guess the Country based on the IP Address.
There are many other even more accurate databases on the market, however since they are shipped under some difficult licenses
so it is sometimes easier to parse them yourself.  
**In case you want to actively use this repository, either fork it or leve an issue so I know.**

This service downloads the inetnum files from all avalable NCCs, extracts the IP addresses sortet by country and optimises it.
The Github Action keeps the list up to date. 

This is a test that should not be merged

Sources:
- `ftp://ftp.arin.net/pub/rr/arin.db.gz`
- `ftp://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-extended-latest`
- `ftp://ftp.apnic.net/pub/apnic/whois/apnic.db.inet6num.gz`
- `ftp://ftp.apnic.net/pub/apnic/whois/apnic.db.inetnum.gz`
- `ftp://ftp.afrinic.net/pub/dbase/afrinic.db.gz`
- `ftp://ftp.ripe.net/ripe/dbase/split/ripe.db.inetnum.gz`
- `ftp://ftp.ripe.net/ripe/dbase/split/ripe.db.inet6num.gz`

The output is grouped in `/pub/{ipVersion}/{country}.txt`

Sample output
Ipv4:
```
5.62.60.4/30
5.62.62.4/30
37.255.187.0/27
45.148.10.0/24
46.24.56.56/30
```

Ipv6:
```
2a02:8060::/31
2a09:4c0:1000::/40
2a0b:4340:51::/48
```
