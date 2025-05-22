from sqlite.spreaddb import SpreadDB

print("hello")
handler = SpreadDB("../../../spread.db")
rslts = handler.get_users(2)
print(rslts)
