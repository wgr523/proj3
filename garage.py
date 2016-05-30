import threading
sync_var = [0,0,0,0] # active reader, waiting reader, active writer, waiting writer
lock = threading.RLock()
okRead = threading.Condition(lock)
okWrite = threading.Condition(lock)
main_mem = {}
time_stamp = [0] # how to use it? use time_stamp[0]

def before_read():
    ''' reader use this to get synchronization'''
    lock.acquire()
    try:
        while sync_var[2]+sync_var[3] > 0:
            sync_var[1]=sync_var[1]+1
            okRead.wait()
            sync_var[1]=sync_var[1]-1
        sync_var[0]=sync_var[0]+1
    finally:
        lock.release()
def after_read():
    lock.acquire()
    try:
        sync_var[0]=sync_var[0]-1
        if sync_var[0]==0 and sync_var[3]>0:
            okWrite.notify()
    finally:
        lock.release()
def before_write():
    with lock: # equivalent to lock.acquire, try, finally
        while sync_var[0]+sync_var[2] > 0:
            sync_var[3]=sync_var[3]+1
            okWrite.wait()
            sync_var[3]=sync_var[3]-1
        sync_var[2]=sync_var[2]+1
def after_write():
    with lock:
        sync_var[2]=sync_var[2]-1
        if sync_var[3] > 0:
            okWrite.notify()
        elif sync_var[1] > 0:
            okRead.notify_all()

        
def insert(key, value):
    if key not in main_mem:
        main_mem[key]=value
        return True
    else:
        return False
def update(key, value):
    if key in main_mem:
        main_mem[key]=value
        return True
    else:
        return False
def delete(key):
    if key in main_mem:
        ret = main_mem[key]
        del main_mem[key]
        return (True,ret)
    else:
        return (False,'error')
def get(key):
    if key in main_mem:
        ret = main_mem[key]
        return (True,ret)
    else:
        return (False,'error')
def countkey():
    return len(main_mem)
def dump():
    return main_mem
def get_time_stamp():
    return time_stamp[0]
def set_time_stamp(t):
    time_stamp[0] = t
def set_main_mem(_main_mem):
    main_mem.clear()
    main_mem.update(_main_mem)
