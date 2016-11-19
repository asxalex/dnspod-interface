#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 asxalex <asxalex@promote.cache-dns.local>
#
# Distributed under terms of the MIT license.

from cmd import Cmd
import getopt
import re
import sys
import json
import dnspod
import time


class Client(Cmd):
    prompt = "dns-op> "
    def __init__(self, api, token):
        self.dns = dnspod.DNSPOD(api, token)
        self.domains = None
        Cmd.__init__(self)
        self.funcMap = {
                "show": self.showMain,
                "use": self.useMain,
                "add": self.addDomain,
                "list": self.listDomain,
                "update": self.updateDomain,
                "delete": self.deleteDomain,
                "exit": self.myexit,
                "help": self.help,
                }
        self.helpfuncMap = {
                "showhelper": self.showhelper,
                "usehelper": self.mainhelper,
                "addhelper": self.addhelper,
                "listhelper": self.listhelper,
                "updatehelper": self.updatehelper,
                "deletehelper": self.deletehelper,
                }
        self.recordType = ["A", "NS", "CNAME"]

    def mainhelper(self):
        res = """
use
    [-i | --index] (M)

"""
        print res

    def showhelper(self):
        res = """
show: show the index and the main domain

"""
        print res

    def addhelper(self):
        res = """
add 
    [-h | --sub_domain] (o)
    [-t | --record_type] default is A (o)
    [-l | --record_line] default is 默认 (o)
    [-T | --ttl] default is 600 (o)
    [-v | --value] the value of the record (M)
    [-s | --status] the status can be [enable | disable], default is enable (o)
    
    """
        print res

    def listhelper(self):
        res = """
list
    [-o | --offset] (o)
    [-l | --length] (o)
    [-k | --keyword] the search keyword of the record, supports the regular expression in python (o)
    [-h | --sub_domain] search for the very sub_domain(o)
    
    """
        print res

    def updatehelper(self):
        res = """
update 
    [-i | --record_id] the record id to be modified (M)
    [-h | --sub_domain] (o)
    [-t | --record_type] default is A (o)
    [-l | --record_line] default is 默认 (o)
    [-T | --ttl] default is 600 (o)
    [-v | --value] the value of the record (M)
    [-s | --status] the status can be [enable | disable], default is enable (o)
    [-C | --confirm] make confirmation on update (M)

    """
        print res

    def deletehelper(self):
        res = """
delete 
    [-i | --record_id] (M)
    [-C | --confirm] make confirmation on deletion (M)
    
    """
        print res

    def usage(self, name):
        self.helpfuncMap[name]()

    def help(self, name=[]):
        name = "" if len(name) == 0 else name[0]
        if name.upper() == "ALL" or name == "":
            self.addhelper()
            self.listhelper()
            self.updatehelper()
            self.deletehelper()
            self.mainhelper()
            self.showhelper()
        else:
            res = self.helpfuncMap.get(name+"helper", None)
            if res != None:
                res()

    def myexit(self, whatever):
        sys.exit(0)

    def addDomain(self, args):
        data = self.argshelper("addhelper", args, "h:t:l:T:v:s:", ["sub_domain", "record_type", "record_line", "ttl", "value", "status"])
        if data is None:
            return
        return self.dns.addDomain(data)
        
    def listDomain(self, args):
        data = self.argshelper("listhelper", args, "o:l:h:k:", ["offset", "length", "sub_domain", "keyword"])
        if data is None:
            return
        return self.dns.listDomain(data)

    def updateDomain(self, args):
        data = self.argshelper("updatehelper", args, "i:h:t:l:v:T:s:C", ["record_id", "sub_domain", "record_type", "record_line", "value", "ttl", "status", "confirm"])
        if data is None:
            return

        if data.get("confirm", 0) == 0:
            return {"status": {"code": -1, "message": "need to use -C to comfirm on deletion"}}
        data.pop("confirm")

        return self.dns.updateDomain(data)

    def deleteDomain(self, args):
        data = self.argshelper("deletehelper", args, "i:C", ["record_id", "confirm"])
        if data is None:
            return
        if data.get("confirm", 0) == 0:
            return {"status": {"code": -1, "message": "need to use -C to comfirm on deletion"}}
        data.pop("confirm")
        return self.dns.deleteDomain(data)

    def useMain(self, args):
        data = self.argshelper("usehelper", args, "i:", ["index"])
        if data is None:
            return
        if len(data) == 0:
            return {"status": {"code": -1, "message": "need to use -i to choose a domain, use show to list the main domain"}}
            
        index = data.pop("index")
        if self.domains is None:
            temp = self.dns.showMainDomain()
            temp = temp.get("domains", None)
            if temp is None:
                print "you don't have a main domain managed by dnspod, please register one first"
            self.domains = temp

        if len(self.domains) == 0:
            print "you don't have a main domain managed by dnspod, please register one first"
            sys.exit(-1)

        index = int(index)
        if (index < 0) or (index >= len(self.domains)):
            return {"status": {"code": -1, "message": "index should be between 0 and %d" % (len(self.domains)-1)}}
        self.dns.domain_id = str(self.domains[index]["id"])
        return

    def showMain(self, args):
        if self.domains is None:
            temp = self.dns.showMainDomain()
            # print temp
            temp = temp.get("domains", None)
            if temp is None:
                print "you don't have a main domain managed by dnspod, please register one first"
                sys.exit(-1)
            self.domains = temp

        for i in range(len(self.domains)):
            print "[%d] %s" % (i, self.domains[i]["punycode"])
        return



    def argshelper(self, cmd, args, argStr, argList):
        if self.domains is None:
            print "show and choose a main domain use [show] and [use] command separately."
            return None
        try:
            opts, argv = getopt.getopt(args, argStr, argList)
        except:
            self.usage(cmd)
            return None

        argstr_single = [letter for letter in argStr if letter != ":"]
        argdict = {}

        for o, a in opts:
            for i in range(len(argstr_single)):
                long_arg = argList[i].strip("=")
                prlong = "--" + long_arg
                short_arg = '-' + argstr_single[i]
                if o in [short_arg, prlong]:
                    argdict[long_arg] = a
        return argdict

    def onecmd(self, args):
        start = time.time()
        command = re.split("[ ]+", args.strip())
        if command[0] == '':
            return
        if not command[0] in self.funcMap.keys():
            print "invalid command"
            return
        res = self.funcMap[command[0]](command[1:])
        if res is None:
            return
        status = res["status"]
        if status["code"] != "1":
            print status["message"]
        else:
            if "record" in res.keys():
                print json.dumps(res["record"], indent=1)
                print "[1 record]"
            elif "records" in res.keys():
                print json.dumps(res["records"], indent=1)
                print "[%d records]" % len(res["records"])
            print "[ok] [%s]" % args
        end = time.time()
        print "[total time]:", end-start


if __name__ == "__main__":
    tid, token = None, None
    try:
        fp = open("apitoken.txt", "r")
        line1 = fp.readline()
        fp.close()
        line1.strip()
        tid, token = line1.split(",")
        tid = tid.strip()
        token = token.strip()
    except:
        print "failed to get id from apitoken.txt..."
        pass

    if len(sys.argv) == 3:
        tid, token = sys.argv[1], sys.argv[2]

    if tid is None or token is None:
        print "plz provide the api token first"
        sys.exit(-1)

    print "use \"help [add | list | update | delete | ALL]\" to get help"
    client = Client(tid, token)
    client.cmdloop()
    #print pingHelper("mon.mon_alarm", ["`field`"], {"a": 1, "b": 2, "limit": 10})

