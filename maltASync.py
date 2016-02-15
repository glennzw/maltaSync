#!/usr/bin/env python
# -*- coding: utf-8 -*-
# glenn@sensepost.com // @glennzw

"""
An attempt to speed Maltego transforms up by making them asynchronous.
Point Maltego at this proxy, select a lot of entities and run a
transform. The following will happen:
* Proxy captures each request and adds it to a queue, with a _uid
* Proxy immediately replies to Maltego with the exact same
  entity that called it, with the addition of a _uid property
* Proxy continuously fires off all transform requests from the
  queue asychronously
* In Maltego re-run the transform at any point and the _uid is
  used to check if the intercepted transform has compelted.

The effect is that when you run a lot of transforms in one go they
all return very quickly, with no change in the graph. Wait a few
seconds and watch the progress in this proxy. Then re-run the transforms
and very quickly all the results come back.

Tests indicate 20% speedup, but need to do more.


TODO: Support for Transform Settings (via TDS)
      Remove UID once successful
      Write Machine to automate
"""

from libmproxy import controller, proxy
from libmproxy.proxy.server import ProxyServer
from libmproxy.models import HTTPResponse
from netlib.http import Headers
import logging
import requests
import uuid
from Maltego import *
import collections
import multiprocessing
import concurrent.futures as cf
from requests_futures.sessions import FuturesSession
import threading
import time

#logging.getLogger("urllib3").setLevel(logging.WARNING)
#logging.basicConfig(level=logging.INFO)

class MaltASync(controller.Master):
    def __init__(self, server, workers):
        controller.Master.__init__(self, server)
        self.letsGo = True
        self.Session = FuturesSession(max_workers=20)
        self.futures = {}
        #self.manager = multiprocessing.Manager()
        #self.futures = self.manager.dict()

    def run(self):  
#        try:
         threading.Thread(target=self.qWatcher).start()
         return controller.Master.run(self)
#        except KeyboardInterrupt:
#            self.letsGo = False
#            self.shutdown()

    def qWatcher(self):
        lastL, lastD = -1, -1
        while self.letsGo:
            time.sleep(2)
            n = 0 
            l = len(self.futures)
            for k,v in self.futures.iteritems():
                if v.done():
                    n+=1
            if lastL != l or lastD != n:
                print "Q: %d, Done: %d" %(l, n)
                lastL = l
                lastD = n

    def handle_request(self, flow):
        if "TransformToRun" in  flow.request.url:
            req_headers = dict(flow.request.headers.fields)
            req_url = flow.request.url
            req_data = flow.request.data.content
        
            m = MaltegoMsg(req_data)
            TRX = MaltegoTransform()
            if not m.getProperty("_uid"):
                uid = str(uuid.uuid4())
                NewEnt = TRX.addEntity(m.Type, m.Value)
                for k,v in m.Properties.iteritems():
                    NewEnt.addProperty(k, k, "nostrict", v)
                NewEnt.addProperty("_uid", "_uid", "nostrict", uid)
                #NewEnt.setNote(uid)
                data = TRX.returnOutput()
    
                #Add to Queue
                future = self.Session.post(req_url, headers=req_headers, data=req_data)
                self.futures[uid] = future
            else:
                #Check status of request
                uid = m.getProperty("_uid")
                futReq = self.futures.get(uid)
                if futReq and futReq.done():
                    del self.futures[uid]
                    data = futReq.result().text
                else:
                    data = TRX.returnOutput() 

        
        resp = HTTPResponse(
                "HTTP/1.1", 200, "OK",
                Headers(Content_Type="text/xml;charset=UTF-8"),
                data)
        
        flow.reply(resp)

if __name__ == "__main__":
    import sys
    workers = 10
    if len(sys.argv) > 1:
        workers = sys.argv[1]
    config = proxy.ProxyConfig(port=8080)
    server = ProxyServer(config)
    ms = MaltASync(server, workers)
ms.run()
