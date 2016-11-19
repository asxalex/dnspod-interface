#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2015 alex <alex@alex>
#
# Distributed under terms of the MIT license.

"""

"""

import urllib
import urllib2
import json
import re
import time

aliasMap = {
        "login_token": "login_token",
        "domain_id": "domain_id",
        "sub_domain": "sub_domain",
        "record_id": "record_id",
        "record_line": "record_line",
        "record_type": "record_type",
        "ttl": "ttl",
        "status": "status",
        "offset": "offset",
        "length": "length",
        "keyword": "keyword",
        "format": "format",
        "value": "value",
        }

def _post(url, dat = {}):
    data = convertData(dat)
    d = urllib.urlencode(data)

    start = time.time()
    result = urllib2.urlopen(url, d)
    end = time.time()
    print "[query time]: ", end-start

    res = result.read()
    return json.loads(res.strip())

def convertData(data):
    temp = {}
    for key in data.keys():
        temp[aliasMap[key]] = data[key]
    return temp
        
def checkType(data, key):
    pass

class DNSPOD(object):
    def __init__(self, tid, token):
        self.token = tid + "," + token
        self.format= "json"
        self.domain_id = ""
        self.recordType = ["A", "NS", "CNAME"]
        self.methodMap = {
                "add": self.addDomain,
                "delete": self.deleteDomain,
                "list": self.listDomain,
                "update": self.updateDomain,
                }

    def getFunc(self, name):
        return self.methodMap.get(name, None)

    def getFuncNames(self):
        return self.methodMap.keys()

    def showMainDomain(self):
        url = "https://dnsapi.cn/Domain.List"
        res = self.post(url, {})
        return res

    def addDomain(self, data):
        url = "https://dnsapi.cn/Record.Create"

        data["record_type"] = data.get("record_type", "A").upper()
        data["ttl"] = data.get("ttl", "60")
        data["record_line"] = data.get("record_line", "默认")

        if not data["record_type"] in self.recordType:
            return {"status": {"code": -1, "message": "type %s is not supported" % data["record_type"]}}
    
        res = self.post(url, data)
        return res

    def listDomain(self, data = {}):
        url = "https://dnsapi.cn/Record.List"
        keys = data.keys()
        key=""
        length=-1
        
        if "length" in keys and key != "":
            length = int(data.pop("length"))

        res = self.post(url, data)

        if res["status"]["code"] != "1":
            return res
       
        if key != "":
            try:
                key = re.compile(key)
            except Exception, e:
                return {"status": {"code": -1, "message": "regular exp error: %s" %e}}
                
            temp = []
            numbers = 0
            for record in res["records"]:
                if key.search(record["name"]) != None or key.search(record["value"]) != None:
                    temp.append(record)
                    numbers += 1
                    if numbers == length:
                        break

            res["records"] = temp
            res["info"]["record_total"] = numbers
        
        return res

    def deleteDomain(self, data):
        url = "https://dnsapi.cn/Record.Remove"

        data["record_id"] = data.get("record_id", -1)
        return self.post(url, data)

    def updateDomain(self, data):
        url = "https://dnsapi.cn/Record.Modify"

        data["record_id"] = data.get("record_id", -1)

        data["record_line"] = data.get("record_line", "默认")
        data["record_type"] = data.get("record_type", "A").upper()
        if data["record_type"] not in self.recordType:
            return {"status": {"code": -1, "message": "type %s is not supported" % data["record_type"]}}
        return self.post(url, data)


    def post(self, url, data):
        data["login_token"] = self.token
        data["format"] = self.format
        data["domain_id"] = self.domain_id
        return _post(url, data)


#######################################################################################################

if __name__ == "__main__":
    dns = DNSPOD()
    dns.listDomain()
