# v 1.0.3 release

import cbcpconf
import cgi
import html
import sys
import codecs
import xlrd
import json

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
func74 = {0: int, 1: str, 2: str, 3: str, 4: float, 5: float}
tab74 = {}

form = cgi.FieldStorage()
text = form.getfirst("VOLUME", "0")
text = html.escape(text)
val = int(text)


wb = xlrd.open_workbook(cbcpconf.xlpath + cbcpconf.xlname['7_4'])
sh_dic_7_4 = wb.sheet_by_name('grunt')

rowcount = sh_dic_7_4.nrows
colcount = sh_dic_7_4.ncols
endrow = rowcount
strow = 1
for row in range(1,rowcount):
    if sh_dic_7_4.row_values(row)[0] == 'start':
        strow = row + 1
        continue
    if sh_dic_7_4.row_values(row)[0] == 'end':
        endraw = row - 1
        break
    if strow > 1 and row >= strow:
        id = 0
        data = []
        toc = colcount if val else 4
        for ii in range(toc):
            if ii == 0:
                id = func74[ii](sh_dic_7_4.row_values(row)[ii])
            else:
                data.append(func74[ii](sh_dic_7_4.row_values(row)[ii]))
        tab74[id] = data
if len(func74.keys()) > 0:
    json_string = json.dumps(tab74)    
    print("Content-type: text\n")
    print(json_string)
else:
    print("Content-type: text\n")
    print('error')