# Purpose

This tool was written to facilitate identification of frontable domains. It mainly targets the Fastly CDN while using the shared certificate, however one can use ```-hh``` parameter to specify a particular host header. It should be pretty snappy since it supports multiprocessing. Just use the ```-h``` flag for help.

# General Logic

```front_brute``` iterates over the lines of an input file containing a simple list of FQDN values, forms a URL from each value, and makes requests via ```requests```. Internal logic expects a url to be constructed druing execution from a list of fully domain names (FQDN), e.g. ```host.domain.tld```, along with values specified by particular parameters.

However, it should be noted that ```front_brute``` expects a response code and status of ```200 OK``` to enable identification of frontable domains. This occurs when a frontable domain makes a successful request to our origin server under our control serving a particular file, just like with any other HTTP request.

# Usage

This section provides details on general logic, important parameters.

## Important Parameters

Though non-conclusive (see ```-h```) the following sections detail important parameters.

### URL Construction via the ```--infile```, ```--protocol```, and ```url_path``` parameters.

The following parameters are used to constuct URLs in the form of: ```<protocol>://<fqdn>/<url_path>```, e.g. ```https://www.offica365.com```.

- ```--infile``` is used to identify a simple list of FQDNs that will be iterated over while brute forcing.
   - A solid starting point is VySec's [DomainFrontingLists](https://github.com/vysec/DomainFrontingLists)
- ```--protocol``` is used to identify the protocol to use during the request, i.e. http or https.
- ```--url-path``` is used to identify the file to request while brute forcing the list of FQDNs.
- ```--origin``` is used to identify the origin host for the Fastly domain
   - _Note_: Overridden by the ```-hh``` parameter

Should an argument to ```-hh``` not be provided, ```front_brute``` expects the ```origin``` argument to be match the one in the service setting of your Fastly service configuration, e.g. ```offica365.global.ssl.fastly.net``` -- which can be shortened to only ```offica365``` since the script'll suffix the remainder of the URL.

## Output

```front_brute``` always writes URLs provoking a 200 status code to stdout. Providing an argument to ```-of``` results in JSON objects written to each line of the targeted outfile.

### JSON Object Structures

The following sections communicate the structure of JSON objects written to disk when the ```-of``` parameter is provided with an argument.

### Successful Transactions (No Python Error Occurred)

The following structure illustrates output stemming from an HTTP transaction that did not produce a Python error. Note that the content member is base64 encoded.

```json
{
    "url":"https://frontable.url.com/test.txt",
    "status_code":200,
    "reason":"OK",
    "content":"c3VjY2Vzcwo="
}
```

#### Failed Transactions (Python Error Occurred)

The following structure illustrates output stemming from an HTTP transaction that produced a Python error.

```json
{
    "url":"https://junk.went.wrong/test.txt",
    "status_code":null,
    "reason":"Unhandled exception when making request.",
    "content":"ERROR MESSAGE"
}
    
```

## Examples

Execute bruteforce with the following (non-obvious) configurations:

- Process count: 5
- Origin: offica365
- Protocol: https
- Capture response content and write to disk in base64 encoded format

```
archangel@deskjet:front_brute~> ./front_brute.py -pc 5 -o offica365 --sleep-time 0 -if Fastly.txt -p https -u /test.txt -of new_output.json --capture-content

[+] Beginning scan
[+] Writing URLs returning a 200 status code to stdout:

https://a.1stdibscdn.com/test.txt
https://academy.ceros.com/test.txt
https://addup.org.cdn.bsd.net/test.txt
https://admin.altmetric.com/test.txt
https://admin.apartmenttherapy.com/test.txt
https://admin.applicaster.com/test.txt
https://admin.astorcosmetics.com/test.txt
https://admin.bedfordandbowery.com/test.txt
https://admin.busbud.com/test.txt
https://admin.ceros.com/test.txt
https://admin.combatgent.com/test.txt
https://admin.coty.com/test.txt
https://admin.cotyconsumeraffairs.com/test.txt
https://admin.disq.us/test.txt
https://admin.dotabuff.com/test.txt
https://admin.drupal.org/test.txt
https://admin.e3expo.com/test.txt
```

# Infrastructure Expections

TL;DR is that a CDN node will proxy a given HTTP request to the origin host specified in the HTTP host header. A server under your control should be listening on the origin host to receive and respond to that request.
