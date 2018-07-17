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

## Painless Introduction to Domain Fronting

Domain fronting is a popular means of hiding the destination of a C2 server/network by exploiting insecure functioning of CDN nodes, which often use the value of the host header embedded in an HTTP request as the FQDN value as they proxy on behalf of CDN consumers. This is achieved by using agent supporing HTTP communication channels that can be configured with a custom host header, such as Meterpreter or Beacon.

Though no expert on how CDNs function, I view CDN nodes (in terms of domain fronting) as proxies that terminate the initial TCP/SSL/TLS connection initiated by a given user agent and proxies the request along to an origin host under control of an attacker using a distinct TCP connection/tunnel initialized by the CDN node. The CDN node consumes the host header, which has been forged/manipulated by the attacker to point to the desired C2 server via hostname, and uses that value as the FQDN for the URL of the proxied request. The path specified in the original URL is appended to the FQDN of the new request, which is then sent to the HTTPS(S) server on the origin host. Upon receipt of a responde from the origin host, the CDN will update appropriate values and forward it back to the user agent over the initial TCP/SSL/TLS connection.

An important constraint becomes clear from the description above: an attacker must be able to control the HTTP host header in order to perform domain fronting. Meterpreter and Cobalt Strike's beacon satisfy this constraint, though it is easier to observe the intricacies using curl. The following text-based diagram illustrates this.

```
--------------------------------------------------------------------------------------------------
| curl Command                                                                                   |
--------------------------------------------------------------------------------------------------
| curl --insecure -v --header "Host: www.offica365.com" https://vulnerable.domain.com/test.txt   |
--------------------------------------------------------------------------------------------------
   |  | <--------[Initial SSL/TLS Tunnel]
   |  |
   |  |        ----------------------------------------------
   |  |        | Request URL: https://vulnerable.domain.com |
   |  |        ----------------------------------------------
   |  |--------| GET /test.txt                              |
   |  |        | Host: www.offica365.com                    |
   |  |        | ...< moar headers >...                     |
   |  |        ----------------------------------------------
   |  |
   |  | <--------[Initial SSL/TLS Tunnel Terminates Here]
----------------------------------------------------------------------------------
| CDN Node                                                                       |
----------------------------------------------------------------------------------
| 1. Receives request                                                            |
| 2. FQDN extracted from host header                                             |
| 3. Path extracted from original URL                                            |
| 4. New URL constructed: {protocol}://{host header FQDN}/{Original URL PATH}    |
| 5. Make request to origin server                                               |
| 6. Upon receit of response, forward back to beacon over initial SSL/TLS Tunnel |
----------------------------------------------------------------------------------
   |  | <--------[New SSL/TLS Tunnel]
   |  |
   |  |        ------------------------------------------
   |  |        | Request URL: https://www.offica365.com |
   |  |        ------------------------------------------
   |  | -------| GET /test.txt                          |
   |  |        | Host: www.offica365.com                |
   |  |        | ...< moar headers >...                 |
   |  |        ------------------------------------------
   |  |
----------------------------------------------------------------------------------
| Origin Host                                                                    |
----------------------------------------------------------------------------------
| 1. Receives request                                                            |
| 2. Responds to CDN node with requested content: success\n                      |
----------------------------------------------------------------------------------
```

Below is verbose output from curl when issuing a similar command:

```
root@somehost:somepath~> curl --insecure --header "Host: offica365.global.ssl.fastly.net" https://vulnerable.domain.com/test.txt
* successfully set certificate verify locations:                                                                                                                                    [0/282]
*   CAfile: /etc/ssl/certs/ca-certificates.crt
  CApath: /etc/ssl/certs
* TLSv1.2 (OUT), TLS header, Certificate Status (22):
* TLSv1.2 (OUT), TLS handshake, Client hello (1):
* TLSv1.2 (IN), TLS handshake, Server hello (2):
* TLSv1.2 (IN), TLS handshake, Certificate (11):
* TLSv1.2 (IN), TLS handshake, Server key exchange (12):
* TLSv1.2 (IN), TLS handshake, Server finished (14):
* TLSv1.2 (OUT), TLS handshake, Client key exchange (16):
* TLSv1.2 (OUT), TLS change cipher, Client hello (1):
* TLSv1.2 (OUT), TLS handshake, Finished (20):
* TLSv1.2 (IN), TLS change cipher, Client hello (1):
* TLSv1.2 (IN), TLS handshake, Finished (20):
* SSL connection using TLSv1.2 / ECDHE-RSA-AES128-GCM-SHA256
* ALPN, server accepted to use h2
* Server certificate:
*  subject: C=US; ST=***; L=*******; O=***** Inc.; CN=*.*****.com
*  start date: Jun 26 00:00:00 2018 GMT
*  expire date: Aug 21 12:00:00 2018 GMT
*  issuer: C=US; O=DigiCert Inc; CN=DigiCert SHA2 Secure Server CA
*  SSL certificate verify ok.
* Using HTTP2, server supports multi-use
* Connection state changed (HTTP/2 confirmed)
* Copying HTTP/2 data in stream buffer to connection buffer after upgrade: len=0
* Using Stream ID: 1 (easy handle 0x563b4dac9c80)
> GET /test.txt HTTP/2
> Host: offica365.global.ssl.fastly.net
> User-Agent: curl/7.57.0
> Accept: */*
>
* Connection state changed (MAX_CONCURRENT_STREAMS updated)!
< HTTP/2 200
< server: SimpleHTTP/0.6 Python/3.6.4
< content-type: text/plain
< last-modified: Mon, 09 Jul 2018 20:10:03 GMT
< accept-ranges: bytes
< date: Fri, 13 Jul 2018 15:47:28 GMT
< via: 1.1 varnish
< x-served-by: cache-dca17736-DCA
< x-cache: MISS
< x-cache-hits: 0
< x-timer: S1531496849.537647,VS0,VE8
< content-length: 8
<
success
* Connection #0 to host vulnerable.domain.com left intact
```
