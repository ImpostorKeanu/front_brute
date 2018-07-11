#!/usr/bin/python3.6

import argparse
import requests
import json
from base64 import b64encode
from multiprocessing import Pool
from time import sleep

import warnings
warnings.filterwarnings("ignore")

def suffix(s,suff="[+]"):
    return f"{suff} {s}"

def sprint(s):
    print(suffix(s))

class Fastly:
    "Needless complexity is needless...."

    SHARED_CERT_PATH = 'global.ssl.fastly.net'

    @staticmethod
    def join_origin(origin):
        "Join the origin with Fastly's shared certificate endpoint"

        return f"{origin}.{Fastly.SHARED_CERT_PATH}"

def request_and_write(pool, args, outfile=None):

    # make the requests and capture the output
    results = pool.map_async(request, args).get()
    # write output to disk
    for result in results:

        # alert on potentially frontable domains
        if result['status_code'] == 200:
            print(result['url'])

        # write output to the output file
        if outfile:
            outfile.write(json.dumps(result)+'\n')

def request(kwargs):
    """
    Make a get request and return a formatted response in the form of a
    dictionary.
    """

    try:

        # ignoring ssl_verify should front_url not begin with https
        if kwargs['front_url'].startswith('https'):

            resp = requests.get(kwargs['front_url'],
                headers=kwargs['headers'],
                timeout=kwargs['request_timeout'],
                verify=kwargs['ssl_verify'])
        else:

            resp = requests.get(kwargs['front_url'],
                headers=kwargs['headers'],
                timeout=kwargs['request_timeout'])

        output = {
            "url":resp.url,
            "status_code":resp.status_code,
            "reason":resp.reason,
        }

        if kwargs['capture_content']:
            output["content"] = b64encode(resp.content).decode('UTF-8')

    except Exception as error:

        output = {
            "url":kwargs['front_url'],
            "status_code":None,
            "reason":"Unhandled exception when making request.",
            "content":str(error)
        }

    return output

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Bruteforce frontable Fastly domains")

    parser.add_argument("--process-count", "-pc", default = 2, type = int,
        help = "Number of processes to use for HTTP requests.")
    parser.add_argument("--origin", "-o", required = True,
        help = """Origin domain associated with the shared Fastly domain. This
        Information can be obtained from from your fastly configuration and
        will follow the following format: <origin>.global.ssl.fastly.net""")
    parser.add_argument("--request-timeout", "-t", type = int, default = 1,
        help = "Period of time to wait for a response to a given HTTP request.")
    parser.add_argument("--ssl-verify", action = "store_true",
        help = "Issue flag should the remote SSL certificate be verified.")
    parser.add_argument("--sleep-time", type = int, default = 1,
        help = "Time to sleep between request waves.")
    parser.add_argument("--capture-content", action = "store_true",
        help = """Determine if HTTP response content should be captured and
        written to the output file""")
    parser.add_argument("--output-file", "-of", default=None,
        help = "File to write JSON output to.")
    parser.add_argument("--input-file", "-if", required = True,
        help = "Input file to read URLs from")
    parser.add_argument("--protocol", "-p", default = "https",
        choices = ["http","https"],
        help = "Determine if http or https should be used.")
    parser.add_argument("--url-path", "-u", required = True,
        help = "File path to be appended to the URL upon request.")
    parser.add_argument("--user-agent", "-ua", 
        help = "User agent to use for requests",
        default = "Mozilla/5.0 (Windows NT x.y; WOW64;"\
            " rv:10.0) Gecko/20100101 Firefox/10.0")
    parser.add_argument("--host-header", "-hh",
        help = "Provide a static host header to be used. Overrides origin.",
        default = None)

    args = parser.parse_args()

    # remove leading slashes to avoid redundant '//' in the url
    if args.url_path[0] == '/':
        args.url_path = args.url_path[1:]

    # configure the http headers for requests
    if not args.origin.endswith(Fastly.SHARED_CERT_PATH) and not args.host_header:
        args.origin = Fastly.join_origin(args.origin)
    elif args.host_header:
        args.origin = args.host_header

    headers = {
        'Host': args.origin,
        'User-Agent': args.user_agent
    }

    infile = open(args.input_file)

    if args.output_file:
        outfile = open(args.output_file, "wt")
    else:
        outfile = None

    if not outfile:
        sprint("Warning: No output file provided. Results "\
            "will not be written to disk.")

    # create a process pool
    pool = Pool(processes = args.process_count)

    # function arguments
    fargs = []

    sprint("Beginning scan")
    sprint("Writing URLs returning a 200 status code to stdout:")
    print()

    for line in infile:

        if line != '':

            url = f"{args.protocol}://{line.strip()}/{args.url_path}"
            fargs.append({
                "front_url": url,
                "headers": headers,
                "request_timeout": args.request_timeout,
                "ssl_verify": args.ssl_verify,
                "capture_content": args.capture_content
            })

        if len(fargs) == args.process_count:

            request_and_write(pool, fargs, outfile)
            fargs.clear()
            sleep(args.sleep_time)

    # request and write any remaining urls
    if len(fargs):
        request_and_write(pool, fargs, outfile)

    print()
    sprint("All URLs checked")

    # ending the pool
    pool.close()
    pool.join()

    # ending file objects
    infile.close()

    if outfile:
        outfile.close()

    # alert the user
    sprint("Scan complete")
    sprint("Exiting")
