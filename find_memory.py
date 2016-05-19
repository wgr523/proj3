import garage
class test():
    def insert(self,s):
        garage.insert(s,'tmp')
    def po(self):
        print(garage.dump())
a = test()
b = test()
a.insert('a')
b.insert('b')
a.po()
