import garage
import os
from threading import Thread

c=[0]
def update():
    for i in range(100000):
        garage.before_write()
        c[0]=c[0]+1
        garage.update('sha',str(c[0]))
        garage.after_write()
    dump()
def dump():
    garage.before_read()
    print(garage.dump())
    garage.after_read()
def fuc():
    update()
    #dump()
if __name__ == "__main__":
    garage.insert('sha','-1')
    lu = 2
    for i in range(lu):
        t = Thread(target = fuc)
        t.start()
