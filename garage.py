main_mem = {}
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
