import os
import signal
with open('conf/primary.pid') as f:
    pid = int(f.readline())
    os.kill(pid, signal.SIGKILL)
    os.remove(f.name)