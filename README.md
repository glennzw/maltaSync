# maltASync: Asynchronous Maltego Transformbobulation
Proxy to intercept Maltego transform requests and fire them upward asynchronously.

## What?
This was an attempt to speed Maltego transforms up by making them asynchronous. Point Maltego at this proxy, select a lot of entities and run a transform. The following will happen:
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

## Usage
```bash
root@boxxx:~/maltaSync# ./maltASync.py 20
[+] Starting Transform proxy with 20 async workers on port 8080...
[+] Starting queue monitor:
    Transforms in Queue: 0. Completed Transforms: 0
    Transforms in Queue: 5. Completed Transforms: 0
    Transforms in Queue: 19. Completed Transforms: 7
    Transforms in Queue: 44. Completed Transforms: 19
    Transforms in Queue: 66. Completed Transforms: 35
    Transforms in Queue: 90. Completed Transforms: 51
    Transforms in Queue: 90. Completed Transforms: 66
    Transforms in Queue: 90. Completed Transforms: 79
    Transforms in Queue: 90. Completed Transforms: 90
```

### TODO
* Support for Transform Settings (via TDS)
* Remove UID once successful
* Write Machine to automate
* Pass through non transform requests
