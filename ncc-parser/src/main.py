import gzip
import timeit

import math
from ipaddress import ip_network, ip_address, summarize_address_range, collapse_addresses
from queue import Queue

import concurrent.futures
import threading
from datetime import datetime, timedelta

thread_local = threading.local()
now = datetime.utcnow()


class Timer:
    """Measure time used."""

    # Ref: https://stackoverflow.com/a/57931660/

    def __init__(self, round_ndigits: int = 0):
        self._round_ndigits = round_ndigits
        self._start_time = timeit.default_timer()

    def __call__(self) -> float:
        return timeit.default_timer() - self._start_time

    def __str__(self) -> str:
        return str(timedelta(seconds=round(self(), self._round_ndigits)))


countries = ["AF", "AX", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR", "AM", "AW", "AU", "AT", "AZ", "BS", "BH",
             "BD", "BB", "BY", "BE", "BZ", "BJ", "BM", "BT", "BO", "BQ", "BA", "BW", "BV", "BR", "IO", "BN", "BG", "BF",
             "BI", "CV", "KH", "CM", "CA", "KY", "CF", "TD", "CL", "CN", "CX", "CC", "CO", "KM", "CG", "CD", "CK", "CR",
             "CI", "HR", "CU", "CW", "CY", "CZ", "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER", "EE", "SZ", "ET",
             "FK", "FO", "FJ", "FI", "FR", "GF", "PF", "TF", "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD", "GP",
             "GU", "GT", "GG", "GN", "GW", "GY", "HT", "HM", "VA", "HN", "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE",
             "IM", "IL", "IT", "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR", "KW", "KG", "LA", "LV", "LB", "LS",
             "LR", "LY", "LI", "LT", "LU", "MO", "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT", "MX",
             "FM", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM", "NA", "NR", "NP", "NL", "NC", "NZ", "NI", "NE", "NG",
             "NU", "NF", "MK", "MP", "NO", "OM", "PK", "PW", "PS", "PA", "PG", "PY", "PE", "PH", "PN", "PL", "PT", "PR",
             "QA", "RE", "RO", "RU", "RW", "BL", "SH", "KN", "LC", "MF", "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS",
             "SC", "SL", "SG", "SX", "SK", "SI", "SB", "SO", "ZA", "GS", "SS", "ES", "LK", "SD", "SR", "SJ", "SE", "CH",
             "SY", "TW", "TJ", "TZ", "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC", "TV", "UG", "UA", "AE",
             "GB", "US", "UM", "UY", "UZ", "VU", "VE", "VN", "VG", "VI", "WF", "EH", "YE", "ZM", "ZW"]


def parse_file(file_name, ipv4_queue: Queue, ipv6_queue: Queue):
    if file_name.endswith('.gz'):
        f = gzip.open(file_name, mode='rt', encoding='ISO-8859-1')
    else:
        f = open(file_name, mode='rt', encoding='ISO-8859-1')

    v4_blocks_by_country = {}
    v6_blocks_by_country = {}
    current_block_network = None
    current_block_country = None
    current_block_ip_version = None

    if file_name.endswith("larnic.db"):
        for line in f:
            line = line.strip()
            if not line.startswith('lacnic'): continue
            elements = line.split('|')
            if elements[1].upper() not in countries: continue
            if elements[2] == 'ipv4':
                ipv4_queue.put(
                    (elements[1], ip_network(elements[3] + '/' + str(int(math.log(4294967296 / int(elements[4]), 2))))))
            elif elements[2] == 'ipv6':
                ipv6_queue.put((elements[1], ip_network(elements[3] + '/' + elements[4])))
            else:
                continue


    else:
        for line in f:
            if line.startswith('%') or line.startswith('#') or line.startswith('remarks:'):
                continue

            line_stripped = line.strip().split("#")[0].strip()
            if line_stripped.startswith('inetnum:'):
                ip_range = line[len('inetnum:'):].strip()
                current_block_network = [ipaddr for ipaddr in summarize_address_range(
                    ip_address(ip_range.split('-')[0].strip()), ip_address(ip_range.split('-')[1].strip()))][0]
                current_block_ip_version = 4
                continue

            if line_stripped.startswith('inet6num:'):
                ip_range = line[len('inet6num:'):].strip()
                current_block_network = ip_network(ip_range)
                current_block_ip_version = 6
                continue

            if line_stripped.startswith('country:') and current_block_network is not None:
                country = line_stripped[len('country:'):].strip().upper()

                if country == 'UNITED STATES':
                    country = 'US'

                if country in countries:
                    current_block_country = country
                continue

            if line_stripped == '' and current_block_network is not None:
                if current_block_country is None:
                    current_block_network = None
                    current_block_ip_version = None
                    continue
                if current_block_ip_version == 4:
                    ipv4_queue.put((current_block_country, current_block_network))
                else:
                    ipv6_queue.put((current_block_country, current_block_network))

                current_block_network = None
                current_block_country = None
                continue

    f.close()
    return [v4_blocks_by_country, v6_blocks_by_country]


def collapse_networks(blocks_by_country):
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as e:
        for country_code, sub_networks in blocks_by_country.items():
            e.submit(collapse_network, blocks_by_country, country_code, sub_networks)


def collapse_network(blocks_by_country, country_code, sub_networks):
    blocks_by_country[country_code] = list(collapse_addresses(sub_networks))
    print("got {} blocks for {}".format(
        len(blocks_by_country[country_code]), country_code))


if __name__ == '__main__':
    timer = Timer()
    SOURCES = [
        "downloads/apnic-v4.gz",
        "downloads/apnic-v6.gz",
        "downloads/afrinic.gz",
        "downloads/arin.db.gz",
        "downloads/larnic.db",
        "downloads/ripe-v4.gz",
        "downloads/ripe-v6.gz",
    ]
    ipv4_write_queue = Queue()
    ipv6_write_queue = Queue()
    ipv4_blocks_by_country = {country_code: [] for country_code in countries}
    ipv6_blocks_by_country = {country_code: [] for country_code in countries}


    def ipv4_worker():
        while True:
            item = ipv4_write_queue.get()
            ipv4_blocks_by_country[item[0]].append(item[1])
            ipv4_write_queue.task_done()


    t = threading.Thread(target=ipv4_worker)
    t.daemon = True
    t.start()


    def ipv6_worker():
        while True:
            item = ipv6_write_queue.get()
            ipv6_blocks_by_country[item[0]].append(item[1])
            ipv6_write_queue.task_done()


    t = threading.Thread(target=ipv6_worker)
    t.daemon = True
    t.start()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for source in SOURCES:
            executor.submit(
                parse_file,
                source,
                ipv4_write_queue,
                ipv6_write_queue
            )

    collapse_networks(ipv4_blocks_by_country)
    collapse_networks(ipv6_blocks_by_country)

    for country_code, ipv4_sub_networks in ipv4_blocks_by_country.items():
        if len(ipv4_sub_networks) < 1: continue
        with open(
                "./pub/v4/{}.txt".format(country_code),
                'w') as handle:
            for network in ipv4_sub_networks:
                handle.write("{}\n".format(str(network)))

    for country_code, ipv6_sub_networks in ipv6_blocks_by_country.items():
        if len(ipv6_sub_networks) < 1: continue
        with open(
                "./pub/v6/{}.txt".format(country_code),
                'w') as handle:
            for network in ipv6_sub_networks:
                handle.write("{}\n".format(str(network)))

    print("handler took {}".format(timer))
