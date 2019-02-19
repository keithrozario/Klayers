'''tldextract CLI'''


import logging

try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution('tldextract').version  # pylint: disable=no-member
except ImportError:
    __version__ = '(local)'
except pkg_resources.DistributionNotFound:
    __version__ = '(local)'

from .tldextract import TLDExtract

try:
    unicode
except NameError:
    unicode = str  # pylint: disable=invalid-name,redefined-builtin


def main():
    '''tldextract CLI main command.'''
    import argparse

    logging.basicConfig()

    parser = argparse.ArgumentParser(
        prog='tldextract',
        description='Parse hostname from a url or fqdn')

    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)  # pylint: disable=no-member
    parser.add_argument('input', metavar='fqdn|url',
                        type=unicode, nargs='*', help='fqdn or url')

    parser.add_argument('-u', '--update', default=False, action='store_true',
                        help='force fetch the latest TLD definitions')
    parser.add_argument('-c', '--cache_file',
                        help='use an alternate TLD definition file')
    parser.add_argument('-p', '--private_domains', default=False, action='store_true',
                        help='Include private domains')

    args = parser.parse_args()
    tld_extract = TLDExtract(include_psl_private_domains=args.private_domains)

    if args.cache_file:
        tld_extract.cache_file = args.cache_file

    if args.update:
        tld_extract.update(True)
    elif len(args.input) is 0:
        parser.print_usage()
        exit(1)

    for i in args.input:
        print(' '.join(tld_extract(i)))  # pylint: disable=superfluous-parens
