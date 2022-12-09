#!/usr/bin/env python

import sys
import json
import shutil
import os.path
import tempfile

if len(sys.argv) < 2:
    print("usage: jsonpp.py filename [ filename ... ]")
    sys.exit(1)

for f in sys.argv[1:]:
    with open(f) as fp:
        data = fp.read()

    obj = json.loads(data)

    with tempfile.TemporaryDirectory() as tmp:
        tmpname = os.path.join(tmp, f)

        with open(tmpname, "w") as fp:
            print(json.dumps(obj, indent=1), file=fp)

        shutil.move(tmpname, f)
