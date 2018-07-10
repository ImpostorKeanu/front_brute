# Purpose

Tool written to facilitate identification of frontable domains. It mainly targets the Fastly CDN while using the shared certificate, however one can use ```-hh``` parameter to specify a particular host header. It should be pretty snappy since it supports multiprocessing. Just use the ```-h```` flag for help.

# Usage

This section provides details on general logic and important parameters.

```fast_brute``` simply iterates over the lines of an input file and makes a request via ```requests```, but it uses multiprocessing to speed things up.

## ```origin``` Parameter

Should an argument to ```-hh``` not be provided, ```fast_brute``` expects the ```origin``` argument to be match the one in the service setting of your Fastly service configuration, e.g. ```offica365.global.ssl.fastly.net``` -- which can be shortened to only ```offica365``` since the script'll suffix the remainder of the URL.

```-hh``` also overrides ```origin```, so be aware of that.

## Output

```fast_brute``` always writes URLs provoking a 200 status code to stdout. Providing an argument to ```-of``` results in JSON objects written to each line of the targeted outfile.

### JSON Object Structures

The following sections communicate the structure of JSON objects written to disk when the ```-of``` parameter is provided with an argument.

#### Successful Transactions (No Python Error Occurred)

The following structure illustrates output stemming from an HTTP transaction that did not produce a Python error.

```json
{
    "url":"https://frontable.url.com/test.txt",
    "status_code":200,
    "reason":"OK",
    "content":"c3VjY2Vzcwo=" # base64 encoded response content
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
archangel@deskjet:front_brute~> ./fast_brute.py -pc 5 -o offica365 --sleep-time 0 -if Fastly.txt -p https -u /test.txt -of new_output.json --capture-content

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
