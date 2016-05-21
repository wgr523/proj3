import os
import signal
with open('conf/backup.pid') as f:
    pid = int(f.readline())
    os.kill(pid, signal.SIGINT)
    os.remove(f.name)
