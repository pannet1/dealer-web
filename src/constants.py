# from sqlite.spreaddb import SpreadDB
from toolkit.fileutils import Fileutils

sec_dir = "../../"
dumpfile = sec_dir + "symbols.json"
XLS = sec_dir + "ao_users.xls"
futil = Fileutils()
alerts_json = "../../alerts.json"

SETG = sec_dir + "settings.yml"
D_SETG = futil.read_file(SETG)

# handler = SpreadDB("../../spread.db")
#
