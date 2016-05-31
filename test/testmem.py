import garage
import os
from threading import Thread

c=[0]
s='sha'
rw = garage.get_rw_create(s)
def update():
    for i in range(100000):
        rw.before_write()
        c[0]=c[0]+1
        garage.update(s,str(c[0]))
        rw.after_write()
    dump()
def dump():
    rw.before_read()
    print(garage.get(s))
    rw.after_read()
def fuc():
    update()
    #dump()
if __name__ == "__main__":
    garage.insert('sha','-1')
    lu = 5
    for i in range(lu):
        t = Thread(target = fuc)
        t.start()
