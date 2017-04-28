#!/usr/bin/nodejs'

var request = require('request');
var md5 = require('md5');
var fs = require('fs');
var extract = require('extract-zip')
var status = require('node-status')
console = status.console()

var artifact_urls = [
  'https://gitlab.com/grase/grase-conf-freeradius/builds/artifacts/master/download?job=trusty-all'  ,
  'https://gitlab.com/grase/grase-conf-freeradius/builds/artifacts/master/download?job=xenial-all',
  'https://gitlab.com/grase/grase-conf-freeradius/builds/artifacts/master/download?job=jessie-all',
  'https://gitlab.com/grase/grase-conf-apache2/builds/artifacts/master/download?job=trusty-all',
  'https://gitlab.com/grase/grase-conf-apache2/builds/artifacts/master/download?job=xenial-all',
  'https://gitlab.com/grase/grase-conf-apache2/builds/artifacts/master/download?job=jessie-all',
  'https://gitlab.com/grase/grase-conf-dnsmasq/builds/artifacts/master/download?job=trusty-all',
  'https://gitlab.com/grase/grase-conf-dnsmasq/builds/artifacts/master/download?job=xenial-all',
  'https://gitlab.com/grase/grase-conf-dnsmasq/builds/artifacts/master/download?job=jessie-all',
  'https://gitlab.com/grase/grase-www-portal/builds/artifacts/hotfix/3.8.1/download?job=trusty-all',
  'https://gitlab.com/grase/grase-www-portal/builds/artifacts/hotfix/3.8.1/download?job=xenial-all',
  'https://gitlab.com/grase/grase-www-portal/builds/artifacts/hotfix/3.8.1/download?job=jessie-all',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=jessie-amd64',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=jessie-armel',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=jessie-armhf',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=jessie-i386',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=trusty-amd64',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=xenial-amd64',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=xenial-i386',
  'https://gitlab.com/grase/coova-chilli/builds/artifacts/grase-1.4.0/download?job=xenial-armhf',
  'https://gitlab.com/grase/grase-conf-squid3/builds/artifacts/squid_3.5/download?job=trusty-all',
  'https://gitlab.com/grase/grase-conf-squid3/builds/artifacts/squid_3.5/download?job=xenial-all',
  'https://gitlab.com/grase/grase-conf-squid3/builds/artifacts/squid_3.5/download?job=jessie-all',
];

download_urls = status.addItem('Download_Urls', {
  max: artifact_urls.length,
  label: "Downloaded"
})
extract_zips = status.addItem('Extract_Zips', {
  max: artifact_urls.length,
  label: "Extracted"
})
status.start({
  pattern: 'Fetching artifacts: {uptime.green} | Downloaded: {Download_Urls.green.bar} | Extracted: {Extract_Zips.cyan.bar}'
})

artifact_urls.forEach(download_extract_url);

function download_extract_url(url) {
  var filename = '/tmp/' + md5(url) + '.zip';
  var url_response;
  request
    .get(url)
    .on('response', function (response) {
      url_response = response;
      //console.log(response.statusCode);
      //console.log(response.headers['content-type']);
    })
    .on('error', function (err) {
      console.log(err);
    })
    .pipe(fs.createWriteStream(filename))
    .on('finish', function() {
      if (url_response.statusCode != 200 ) {
        console.log("Error fetching " + url + ". Status: " + url_response.statusCode)
        download_urls.inc()
        extract_zips.max = extract_zips.max - 1
      } else {
        //console.log("Finished downloading " + url)
        download_urls.inc()
        extract(filename, {dir: '/home/tim/grase/aptly.incoming/artifacts/'}, function (err) {
          if(err) {
            console.log("Failed to extract " + filename);
            console.log(err);
          } else {
            //console.log("Extraction of " + filename + " finished.");
            extract_zips.inc()
          }
         })
      }
    });
}

var checkFinished = setInterval(function(){
  if (download_urls.count >= download_urls.max) {
    status.stop();
    console.log();
    console.log("All urls downloaded");
    clearInterval(checkFinished);
  }
}, 1000)
