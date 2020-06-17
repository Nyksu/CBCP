title = '''
CBCP (Calculation of the bearing capacity of piles)
Программа для расчёта несущей способности свай в талых грунтах
СП 24.13330.2011 (Свайные фундаменты)
NykSu (c) май 2020.  v 1.0.3 b web
GitHub NykSu
'''
import cbcpconf
import htmlbuilder as hb
import cgi
import html
import sys
import codecs
import xlrd
import json


class graundLayers:
    layers = {}
    ids = set()

    def getsteckdepth():
        result = 0
        if len(graundLayers.layers) > 0:
            for l in graundLayers.layers.values():
                result += l.depth
        return result
    
    def getLayerByH(h):
        lr = None
        hstack = 0
        for l in graundLayers.layers.values():
            hstack += l.depth
            if hstack > h:
                lr = l
                break
            elif hstack == h:
                l.depth += 0.005
                hstack += 0.005
                lr = l
                break
        return [lr, hstack]

    def __init__(self, depth, material, tid, fluidity):
        self.id = len(graundLayers.ids) + 1
        graundLayers.ids.add(self.id)
        self.depth = depth
        self.middle = graundLayers.getsteckdepth() + depth / 2
        self.material = material
        self.tid = tid
        self.fluidity = fluidity
        graundLayers.layers[self.id] = self


class Catalog:
    codes = {}
    
    def __init__(self, code, sort, iseasy, interpol, opinterpol):
        self.code = code
        self.iseasy = iseasy
        self.interpol = interpol
        self.sort = sort
        self.titles = []
        self.operators = []
        self.strow = 1
        self.endraw = 0
        self.endcol = 0
        self.opinterpol = opinterpol
        self.data = []
        self.caption = ''
        self.captionplus = ''
        Catalog.codes.update({(code, sort): self})

def getInterpol(self, neoper, fluidity, reserror = -1):
        result = reserror # возвращает при ошибке
        try:
            fluidlist = list(map(float, self.titles))
        except:
            return result
        if fluidity <= fluidlist[0]:
            return self.getNear(neoper, 0, -2)
        elif fluidity >= fluidlist[-1]:
            idx = len(fluidlist) - 1
            return self.getNear(neoper, idx, -3)
        mindelta = 100000
        idx = -1
        idn = -1
        for i in range(len(fluidlist)):
            if abs(fluidity - fluidlist[i]) < mindelta:
                mindelta = abs(fluidity - fluidlist[i])
                idx = i
                if fluidity < fluidlist[i]:
                    idn = i - 1
                else:
                    idn = i
        if mindelta < 0.002:
            return self.getNear(neoper, idx, -4)
        r1 = self.getNear(neoper, idn, -5)
        r2 = self.getNear(neoper, idn + 1, -6)
        if r1 > 0 and r2 > 0:
            result = (r2 - r1) * (fluidity - fluidlist[idn]) / (fluidlist[idn + 1] - fluidlist[idn]) + r1
        return result
    
    def getNear(self, neoper, titlnom, reserror = -10):
        result = reserror # возвращает при ошибке
        if not self.interpol:
            return self.getSharp(neoper, titlnom, -11)
        elif self.titles[titlnom][0] == '@':
            return result
        if neoper > 40:
            return result
        mindelta = 100000
        idx = -1
        for i in range(len(self.operators)):
            if abs(neoper - self.operators[i]) < mindelta:
                mindelta = abs(neoper - self.operators[i])
                if neoper < self.operators[i] and i > 0:
                    idx = i - 1
                else:
                    idx = i
        if mindelta < 0.01:
            if abs(neoper - self.operators[idx]) <= mindelta:
                return self.data[idx][titlnom]
            else:
                return self.data[idx + 1][titlnom]
        result = (self.data[idx + 1][titlnom] - self.data[idx][titlnom]) 
        result *= abs(neoper - self.operators[idx])/(self.operators[idx + 1] - self.operators[idx])
        result += self.data[idx][titlnom]
        return result
    
    def getSharp(self, oper, titlnom, reserror = -20):
        idx = -1
        for i in range(len(self.operators)):
            if abs(oper - self.operators[i]) < 0.001:
                idx = i
                break
        if idx >= 0:
            return self.data[idx][titlnom]
        else:
            return reserror
    
    def addcatTitle(self, name):
        self.titles.append(name)

    def addcatOperator(self, value):
        self.operators.append(value)
    
    def Tcount(self):
        return len(self.titles)

    def Rcount(self):
        return len(self.operators)

    def LoadData(self, sheet):
        for row in range(self.strow, self.endraw + 1):
            rr = []
            for col in range(1, self.endcol):
                if self.titles[col-1][0] == '@':
                    rr.append(str(sheet.row_values(row)[col]))
                else:
                    rr.append(float(sheet.row_values(row)[col]))
            if len(rr) > 0:
                self.data.append(rr)

    def setupFromSheet(self, sheet):
        rowcount = sheet.nrows
        colcount = sheet.ncols
        self.endrow = rowcount
        for row in range(self.strow,rowcount):
            if sheet.row_values(row)[0] == 'start':
                self.strow = row + 1
            if sheet.row_values(row)[0] == 'end':
                self.endraw = row - 1
                break
            if self.strow > 1 and row >= self.strow:
                if self.iseasy:
                    self.addcatOperator(float(sheet.row_values(row)[0]))
                else:
                    self.addcatOperator(int(sheet.row_values(row)[0]))
        self.endcol = colcount
        for col in range(1, colcount):
            if sheet.row_values(self.strow-1)[col] == '':
                self.endcol = col-1
                break
            self.addcatTitle(str(sheet.row_values(self.strow-1)[col]))
        self.LoadData(sheet)
        # row, col = [int(i) for i in conf.get(self.code, 'captionpos').split(',')] 
        row, col = cbcpconf.captions[self.code]['pos']
        self.caption = sheet.row_values(row)[col]   
        stt = conf.get(self.code, 'captionplus')
        if stt != '@':
            row, col = [int(i) for i in stt.split(',')]
            self.captionplus = sheet.row_values(row)[col]

def SafeGetFromForm(form, parname, default, func):
    text = form.getfirst(parname, default)
    text = html.escape(text)
    return func(text)

def CalcPile(Gamma_C, svaiaL, svaiaS, svaiaP, svaiaO, KN, hNoCalc):
    result = -100
    R = 0
    cat7_2sand = Catalog.codes[('7_2', 'sand')]
    cat7_2clay = Catalog.codes[('7_2', 'clay')]
    cat7_3sand = Catalog.codes[('7_3', 'sand')]
    cat7_3clay = Catalog.codes[('7_3', 'clay')]
    cat7_4 = Catalog.codes[('7_4', 'grunt')]
    
    Grr =  cat7_4.data[cat7_4.operators.index(svaiaO)][3]
    Fde = svaiaS * Grr 
    lll = graundLayers.getLayerByH(svaiaL)    
    if lll[0].tid < 0:
        R = cat7_2clay.getInterpol(svaiaL, lll[0].fluidity)
    else:
        R = cat7_2sand.getNear(svaiaL, lll[0].tid)
    if R < 0:
        #raise ValueError("Ошибка интерполяции для таблицы 7.2; code = " + str(R))
        return R
    Fde *= R
    Fds = 0
    if hNoCalc > 0:
        lNc = graundLayers.getLayerByH(hNoCalc)
    for lr in graundLayers.layers.values():
        if lr.middle >= lll[0].middle:
            break
        f = 0
        lrmiddle = lr.middle
        lrdepth = lr.depth
        if hNoCalc > 0:
            if lr.middle < lNc[0].middle:
                # 'Слой пропущен целиком'
                continue
            elif lr.middle == lNc[0].middle:
                lrdepth = lNc[1] - hNoCalc 
                lrmiddle = lNc[1] - lrdepth / 2
                # 'Слой не весь учтён. Толщина слоя уменьшина 
        if lr.tid < 0:
            f = cat7_3clay.getInterpol(lrmiddle, lr.fluidity)
        else:
            f = cat7_3sand.getNear(lrmiddle, lr.tid)
        if f < 0:            
            return f
        Fff = f * lrdepth * cat7_4.data[cat7_4.operators.index(svaiaO)][4]
        print(lr.id, round(lrmiddle, 2), round(f, 2), round(lrdepth, 2), 
              cat7_4.data[cat7_4.operators.index(svaiaO)][4], round(Fff, 2))
        Fds += Fff
    midHLast = lll[1] - lll[0].depth + (lll[0].depth - (lll[1] - svaiaL)) / 2
    f = 0
    if lll[0].tid < 0:
        f = cat7_3clay.getInterpol(midHLast, lll[0].fluidity)
    else:
        f = cat7_3sand.getNear(midHLast, lll[0].tid)
    if f < 0:
        return f
    Fff = f * (lll[0].depth - (lll[1] - svaiaL)) * cat7_4.data[cat7_4.operators.index(svaiaO)][4]
    print(lll[0].id, round(midHLast, 2), round(f, 2), round(lll[0].depth - (lll[1] - svaiaL), 2), 
          cat7_4.data[cat7_4.operators.index(svaiaO)][4], round(Fff, 2))
    Fds += Fff
    Fds *= svaiaP
    Fds *= Gamma_C
    Fde *= Gamma_C
    F_d = Fds + Fde
    Fdp = F_d / KN
    result = [F_d, Fds, Fde, Fdp]
    return result

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

hpgerr = hb.htmlpage('error', cbcpconf.htmlResTop, cbcpconf.htmlResFoot, False)
results = {'errors': [], 'title': [], 'indata': {}, 'captions': [], 'reslines': []}

cat7_2sand = Catalog('7_2', 'sand', True, True, False)
cat7_2clay = Catalog('7_2', 'clay', True, True, True)
cat7_3sand = Catalog('7_3', 'sand', True, True, False)
cat7_3clay = Catalog('7_3', 'clay', True, True, True)
cat7_4 = Catalog('7_4', 'grunt', False, False, False)

wb = xlrd.open_workbook(cbcpconf.xlpath + cbcpconf.xlname[cat7_2sand.code])
sh_dic = wb.sheet_by_name(cat7_2sand.sort)
cat7_2sand.setupFromSheet(sh_dic)        

wb = xlrd.open_workbook(cbcpconf.xlpath + cbcpconf.xlname[cat7_2clay.code])
sh_dic = wb.sheet_by_name(cat7_2clay.sort)
cat7_2clay.setupFromSheet(sh_dic)

wb = xlrd.open_workbook(cbcpconf.xlpath + cbcpconf.xlname[cat7_3sand.code])
sh_dic = wb.sheet_by_name(cat7_3sand.sort)
cat7_3sand.setupFromSheet(sh_dic)

wb = xlrd.open_workbook(cbcpconf.xlpath + cbcpconf.xlname[cat7_3clay.code])
sh_dic = wb.sheet_by_name(cat7_3clay.sort)
cat7_3clay.setupFromSheet(sh_dic)

wb = xlrd.open_workbook(cbcpconf.xlpath + cbcpconf.xlname[cat7_4.code])
sh_dic = wb.sheet_by_name(cat7_4.sort)
cat7_4.setupFromSheet(sh_dic)

hpg = hb.htmlpage('calc', cbcpconf.htmlResTop, cbcpconf.htmlResFoot, False)

form = cgi.FieldStorage()
# Слои почвы
cutLayer = SafeGetFromForm(form, "CUTLAYER", "0", int)
layercount = SafeGetFromForm(form, "LAYERCOUNT", "0", int)
if layercount == 0:
    hpgerr.addString('', '', '<h1>Ошибка</h1> <h3>Нет ни однго слоя.</h3>', False)
    results['errors'].append('Нет ни однго слоя') 
    hpgerr.printHTML()
    sys.exit()
results['indata']['grunt'] = []
for ii in range(0,layercount):
    snom = str(ii)
    if ii <10:
        snom = '0' + snom
    grunt = SafeGetFromForm(form, "GRUNT" + snom, "", str)
    if grunt == "":
        hpgerr.addString('', '', '<h1>Ошибка</h1> <h3>Нет типа слоя.</h3>', False)
        results['errors'].append('Нет типа слоя.') 
        hpgerr.printHTML()
        sys.exit()
    tid = SafeGetFromForm(form, "TID" + snom, "-1", int)
    val = SafeGetFromForm(form, "VAL" + snom, "0", float)
    fluid = SafeGetFromForm(form, "FLUID" + snom, "0", float)    
    results['indata']['grunt'].append((round(Fdse[0] / G, 2), 'тонн', 'Расчётная, полная несущая способность Fd = '))
    if cutLayer > 0 and val > cutLayer:
        for vv in range(cutLayer,int(val+1), cutLayer):
            graundLayers(cutLayer, grunt, tid, fluid)
        if val - vv * cutLayer > 0:
            graundLayers(val - vv * cutLayer, grunt, tid, fluid)
    else:
        graundLayers(val, grunt, tid, fluid)
hlayers = graundLayers.getsteckdepth()
hNoCalc = SafeGetFromForm(form, "HNOCALC", "0", float)
results['indata']['HNOCALC'] = (hNoCalc, 'м', 'Неучитываемый в расчёте верхний слой почвы:')
# Параметры сваи
svaiaNG = SafeGetFromForm(form, "SVAIANG", "1", float)
results['indata']['SVAIANG'] = (svaiaNG, '', 'Коэффициент надежности по грунтам:')
svaiaN = SafeGetFromForm(form, "SVAIAN", "1", float)
results['indata']['SVAIAN'] = (svaiaN, '', 'Коэффициент надежности сооруженияа:')
KN = svaiaN * svaiaNG
svaiaT = SafeGetFromForm(form, "SVAIAT", "1", int)
if svaiaT:
    results['indata']['SVAIAT'] = ('Квадрат', '', 'Форма сечения сваи:')
else:
    results['indata']['SVAIAT'] = ('Круг', '', 'Форма сечения сваи:')
svaiaR = SafeGetFromForm(form, "SVAIAR", "1", float)
svaiaS = svaiaR * svaiaR
svaiaP = svaiaR * 4
if not svaiaT:
    svaiaS = svaiaS * 3.14 / 4
    svaiaP = svaiaR * 3.14
results['indata']['SVAIAS'] = (svaiaS, 'кв.м', 'Площадь сечения сваи:')
results['indata']['SVAIAP'] = (svaiaP, 'м', 'Периметр сечения сваи:')
svaiaС = SafeGetFromForm(form, "SVAIAC", "1", int)
svaiaL = SafeGetFromForm(form, "SVAIAL", "1", float)
if svaiaС:
    results['indata']['SVAIAC'] = ('подбор длины сваи', '', 'Выбора вида расчётов:')
else :
    results['indata']['SVAIAC'] = ('расчёт сваи', '', 'Выбора вида расчётов:')
if svaiaL < 3:
    svaiaL = 3
if abs(hlayers - svaiaL) < 0.05:
    graundLayers.layers[-1].depth += 0.1
    hlayers += 0.1
results['indata']['SVAIAL'] = (svaiaL, 'м', 'Длина сваи:')
results['indata']['HLAYERS'] = (hlayers, 'м', 'Общая глубина введённых слоёв грунта:')
if hlayers < svaiaL:
    hpgerr.addString('', '', '<h1>Ошибка</h1> <h3>Глубина слоёв меньше длины сваи.</h3>', False)
    results['errors'].append('Глубина слоёв меньше длины сваи.') 
    hpgerr.printHTML()
    sys.exit()
# Коэффициент, согласно способа погружения сваи
svaiaO = SafeGetFromForm(form, "SVAIAO", "1", int)
results['indata']['SVAIAO'] = (svaiaO, '', 'Коэффициент согласно способа погружения сваи:')
# Прочие коэффициенты
Gamma_C = SafeGetFromForm(form, "GAMMA_C", "1", float)
results['indata']['GAMMA_C'] = (Gamma_C, '', 'Коэффициент Gamma_C:')
G = SafeGetFromForm(form, "G", "10", float)
results['indata']['G'] = (G, '', 'Коэффициент перевода кН в тонны G:')

# 
svaiaF = SafeGetFromForm(form, "SVAIAF", "1", float) # желаемая несущая способность при подборе длины сваи
svaiaFT = SafeGetFromForm(form, "SVAIAFT", "1", int) # При подборе выбор - только по боковой поверности или полная несущая
if svaiaFT:
    results['indata']['SVAIAF'] = (svaiaF, 'тонн', 'желаемая несущая способность по боковой поверхности при подборе длины сваи:')
else:
    results['indata']['SVAIAF'] = (svaiaF, 'тонн', 'желаемая полная несущая способность при подборе длины сваи:')
# Блок расчётов. Расчёт сваи.
LPile = svaiaL
if svaiaС:
    svaiaF *= G    
    while True:
        Fdse = CalcPile(Gamma_C, LPile, svaiaS, svaiaP, svaiaO, KN, hNoCalc)
        if type(Fdse) == int:
            hpgerr.addString('', '', '<h1>Ошибка</h1> <h3>Глубина слоёв меньше длины сваи. № {} </h3>'.format(str(Fdse)), False)
            results['errors'].append('Глубина слоёв меньше длины сваи.') 
            hpgerr.printHTML()
            sys.exit()
        ss = ''
        if Fdse[svaiaFT] <= svaiaF:
            LPile += 0.5
            if hlayers <= LPile:
                hpgerr.addString('', '', '<h1>Ошибка</h1> <h3>Сведений по слоям грунта не хватает для увеличения длины сваи. Подбор прекращён.</h3>', False)
                results['errors'].append('Сведений по слоям грунта не хватает для увеличения длины сваи. Подбор прекращён.') 
                hpgerr.printHTML()
                sys.exit()
            continue
        else:
            if abs(Fdse[svaiaFT] - svaiaF)/svaiaF > 0.05:
               LPile -= 0.2
                if LPile < 3:
                    hpgerr.addString('', '', '<h1>Ошибка</h1> <h3>Свая не может быть уменьшена. Придел расчётов 3м. Подбор прекращён.</h3>', False)
                    results['errors'].append('Свая не может быть уменьшена. Придел расчётов 3м. Подбор прекращён.') 
                    hpgerr.printHTML()
                    sys.exit()
                continue
            else:
                break
else:
    Fdse = CalcPile(Gamma_C, svaiaL, svaiaS, svaiaP, svaiaO, KN, hNoCalc)
    if type(Fdse) == int:
        hpgerr.addString('', '', '<h1>Ошибка</h1> <h3>Ошибка расчёта или интерполяции; code ={}</h3>'.format(str(Fdse)), False)
        results['errors'].append('Глубина слоёв меньше длины сваи.') 
        hpgerr.printHTML()
        sys.exit()

results['title'].append('Расчёт удачно закончен!')
if svaiaС:
    results['title'].append('Длина сваи определена.')
results['captions'].append('Исходные данные расчёта:')
results['captions'].append('Результаты расчёта:')
results['reslines'].append((round(Fdse[0] / G, 2), 'тонн', 'Расчётная, полная несущая способность Fd = '))
if svaiaС:
    results['reslines'].append((round(LPile, 2), 'метров', 'Искомая длина сваи = '))
results['reslines'].append((round(Fdse[2] / G, 2), 'тонн', 'Несущая способность грунта под нижним концом сваи = '))
results['reslines'].append((round(Fdse[1] / G, 2), 'тонн', 'Несущая способность грунта по боковой поверхности сваи = '))
results['reslines'].append((round(Fdse[3] / G, 2)), 'тонн', 'Предельно допустимая нагрузка = '))

hpg.addString('', '', '<h1>{}</h1> <h3>{}</h3>'.format(results['title'][0], results['title'][1]), False)
hpg.addString('', '', '<p>{}<p>'.format(results['captions'][0]), False)
hpg.addStringsData(results['indata']) # исходные данные 
hpg.addString('', '', '<p>{}<p>'.format(results['captions'][1]), False)
hpg.addStringsData(results['reslines']) # результаты рассчетов

prnJSON = SafeGetFromForm(form, "JSON", "0", int)
if prnJSON:
    json_string = json.dumps(results)
    print(json_string)
else:
    hpg.printHTML