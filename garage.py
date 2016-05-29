import time
main_mem = {}
time_stamp = [0] # how to use it? use time_stamp[0]
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
