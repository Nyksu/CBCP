title = '''
CBCP (Calculation of the bearing capacity of piles)
Программа для расчёта несущей способности свай в талых грунтах
СП 24.13330.2011 (Свайные фундаменты)
NykSu (c) май 2020.  v 1.0.1
GitHub NykSu
'''

# Программа рассёта свай на талых грунтах.

import xlrd
import os
import sys
import configparser

struct = {'sand' : [0, 'песчаные грунты', 'песчаного грунта', 'песка'], 
          'clay' : [1, 'глинистые грунты', 'глинистого грунта', 'глины']}

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

    def setupFromSheet(self, sheet, conf):
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
        row, col = [int(i) for i in conf.get(self.code, 'captionpos').split(',')] 
        self.caption = sheet.row_values(row)[col]   
        stt = conf.get(self.code, 'captionplus')
        if stt != '@':
            row, col = [int(i) for i in stt.split(',')]
            self.captionplus = sheet.row_values(row)[col]

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
                print(lr.id, lrmiddle, lNc[0].middle, 'Слой пропущен целиком', lrdepth)
                continue
            elif lr.middle == lNc[0].middle:
                lrdepth = lNc[1] - hNoCalc 
                lrmiddle = lNc[1] - lrdepth / 2
                print(lr.id, round(lr.middle, 2), 'Слой не весь учтён. Толщина слоя уменьшина с', 
                      round(lr.depth, 2), 'до', round(lrdepth, 2), 'м')
        if lr.tid < 0:
            f = cat7_3clay.getInterpol(lrmiddle, lr.fluidity)
        else:
            f = cat7_3sand.getNear(lrmiddle, lr.tid)
        if f < 0:
            # raise ValueError("Ошибка интерполяции для таблицы 7.3; code = " + str(f))
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
        # raise ValueError("Ошибка интерполяции для таблицы 7.3; code = " + str(f))
        return f
    Fff = f * (lll[0].depth - (lll[1] - svaiaL)) * cat7_4.data[cat7_4.operators.index(svaiaO)][4]
    print(lll[0].id, round(midHLast, 2), round(f, 2), round(lll[0].depth - (lll[1] - svaiaL), 2), 
          cat7_4.data[cat7_4.operators.index(svaiaO)][4], round(Fff, 2))
    Fds += Fff
    Fds *= svaiaP
    # Fde = F_d
    Fds *= Gamma_C
    Fde *= Gamma_C
    F_d = Fds + Fde
    Fdp = F_d / KN
    result = [F_d, Fds, Fde, Fdp]
    return result

if __name__ == "__main__":
    
    print(title)

    base_path = os.path.dirname(os.path.abspath(__file__))  # os.getcwd()
    ini_conf_name = 'CBCP.ini'
    
    if not os.path.exists(os.path.join(base_path, ini_conf_name)):
        sys.exit('Не найден файл конфигурации: ' + os.path.join(base_path, ini_conf_name))
    
    config = configparser.ConfigParser()
    config.read(os.path.join(base_path, ini_conf_name))
    confCat = "CATALOGS"
    xlpath = config.get("PATH", 'xlspath')

    cat7_2sand = Catalog('7_2', 'sand', True, True, False)
    cat7_2clay = Catalog('7_2', 'clay', True, True, True)
    cat7_3sand = Catalog('7_3', 'sand', True, True, False)
    cat7_3clay = Catalog('7_3', 'clay', True, True, True)
    cat7_4 = Catalog('7_4', 'grunt', False, False, False)

    wb = xlrd.open_workbook(xlpath + config.get(confCat, cat7_2sand.code))
    sh_dic = wb.sheet_by_name(cat7_2sand.sort)
    cat7_2sand.setupFromSheet(sh_dic, config)        

    wb = xlrd.open_workbook(xlpath + config.get(confCat, cat7_2clay.code))
    sh_dic = wb.sheet_by_name(cat7_2clay.sort)
    cat7_2clay.setupFromSheet(sh_dic, config)

    wb = xlrd.open_workbook(xlpath + config.get(confCat, cat7_3sand.code))
    sh_dic = wb.sheet_by_name(cat7_3sand.sort)
    cat7_3sand.setupFromSheet(sh_dic, config)

    wb = xlrd.open_workbook(xlpath + config.get(confCat, cat7_3clay.code))
    sh_dic = wb.sheet_by_name(cat7_3clay.sort)
    cat7_3clay.setupFromSheet(sh_dic, config)
    
    wb = xlrd.open_workbook(xlpath + config.get(confCat, cat7_4.code))
    sh_dic = wb.sheet_by_name(cat7_4.sort)
    cat7_4.setupFromSheet(sh_dic, config)

    print(cat7_2sand.Rcount(), cat7_2clay.Rcount(), 'Загружена таблица 7.2')    
    print(cat7_3sand.Rcount(), cat7_3clay.Rcount(), 'Загружена таблица 7.3')
    print(cat7_4.Rcount(), cat7_4.Tcount(), 'Загружена таблица 7.4')
    print()
    
    print('Вводим слои грунтов.')
    cutLayer = int(input('Делить слои грунтов на части? Нет - 0, делить на 1м - 1, делить на 2м - 2: '))
    hlayers = 0
    hNoCalc = 0
    while True:
        print('Новый слой.')
        print('Выбирите тип грунта: ')
        for tt in struct.values():
            print(tt[1],'- введите ', tt[0])
        ii = int(input('0 или 1? Сделайте выбор: '))
        if 0 == ii or ii == 1:
            grunt = list(struct.keys())[ii]
        else:
            print('Ошибка выбора типа грунта.')
            continue
        print()
        print('Уточните параметры ', struct[grunt][2])
        if not Catalog.codes[('7_2', grunt)].opinterpol:
            print('Из каких типов', struct[grunt][3],' состоит слой (введите номер):')
        else:
            print('Табличные значения: ', end = ' ')
        for i in range(len(Catalog.codes[('7_2', grunt)].titles)):
            if not Catalog.codes[('7_2', grunt)].opinterpol:
                print(Catalog.codes[('7_2', grunt)].titles[i], ' = ', i)
            else:
                print(Catalog.codes[('7_2', grunt)].titles[i], end = ' ')
        if not Catalog.codes[('7_2', grunt)].opinterpol:
            tid = int(input('Введите номер типа: '))
            fluid = 0
        else:
            print()
            fluid = float(input('Введите показатель текучести ' + struct[grunt][2] + ': '))
            tid = -1
        print('Введите мощность текущего слоя', struct[grunt][2])
        val = float(input('в метрах: '))
        if val == 0:
            print('Завершение ввода слоёв грунта.')
            break
        if cutLayer > 0 and val > cutLayer:
            for vv in range(cutLayer,int(val+1), cutLayer):
                graundLayers(cutLayer, grunt, tid, fluid)
            if val - vv * cutLayer > 0:
                graundLayers(val - vv * cutLayer, grunt, tid, fluid)
        else:
            graundLayers(val, grunt, tid, fluid)
        print('Номера ввёденных слоёв:', *list(graundLayers.layers.keys()))
        print()
        ii = int(input('Введите 1 для добавления слоя или 0 для закрытия слоёв грунта: '))
        print()
        hlayers = graundLayers.getsteckdepth()
        if ii == 0:
            if hlayers < 3:
                print('Не достаточная для расчётов глубина набора грунтов! Введите еще слои грунтов.')
                continue
            print('Завершение ввода слоёв грунта.')
            break
    print('Общая грубина введённых слоёв грута:', hlayers, '(м)')
    print()

    print('Блок задания верхнего не учитываемого в расчёте слоя грунта')
    print('Возможные причины: слой торфа, пучинистый грунт.')
    print('При вводе 0 - блок не будет оказывать влияние (так же можно пропустить блок)')
    hNoCalc = float(input('Введите глубину верхнего не учитываемого грута (м): '))
    print()

    print('Ввод коэффициентов надежности.')
    svaiaNG = float(input('Введите коэффициент надежности по грунтам: '))
    svaiaN = float(input('Введите коэффициент надежности сооружения: '))
    KN = svaiaN * svaiaNG
    
    print('Ввод параметров сваи.')
    svaiaT = 0
    ii = int(input('0 - круглого или 1 - квадратного сечения свая? Сделайте выбор: '))
    if ii != 0:
        svaiaT = 1
    if svaiaT:
        svaiaR = float(input('Введите длину стороны сечения сваи (м): '))
    else:
        svaiaR = float(input('Введите диаметр сечения сваи (м): '))
    svaiaS = svaiaR * svaiaR
    svaiaP = svaiaR * 4
    if not svaiaT:
        svaiaS = svaiaS * 3.14 / 4
        svaiaP = svaiaR * 3.14
    print('Площадь сечения сваи (кв.м):', svaiaS)
    print('Периметр сечения сваи (м):', svaiaP)
    print()

    print('Длина сваи вводится от уровня прирожного рельефа.')
    svaiaС = int(input('0 - расчёт длины или 1 - подбор длины сваи? Сделайте выбор: '))
    if svaiaС:
        svaiaL = float(input('Введите ориентировочно начальную длину сваи для подбора (м): '))
    else:
        svaiaL = float(input('Введите точную длину сваи для расчёта (м): '))
    if svaiaL < 3:
        print('Длина сваи меньше 3 м. Данная программа может считать сваи длиной более 3х метров.')
        print('Увеличиваем длину сваи до 3х метров')
        svaiaL = 3
    if hlayers <= svaiaL:
        raise ValueError("Ошибка! Длина сваи меньше глубины введённых слоёв. Глубина слоёв" + str(hlayers))
    print()

    # Выбор коэффициентов из таблицы 7.4
    svaiaO = -1
    print('Выбираем', cat7_4.captionplus)
    print(cat7_4.caption)
    for op in cat7_4.operators:
        deep = len(str(op))
        ii = cat7_4.operators.index(op)
        if deep == 2:
            print()
            print(cat7_4.data[ii][0])
            if not int(input('0 - перейти к следующему 1 - выбор текущего пункта. Сделайте выбор: ')):
                continue
            else:
                svaiaO = op
                break
        elif deep == 3:
            if str(op)[1] == '1':
                print()
                print(cat7_4.data[ii][0])
            print(cat7_4.data[ii][1], '=', str(op)[1])
            if str(op)[2] == '0':
                acc = int(input('0 - перейти к следующему пункту  от 1 до ' + str(op)[1] 
                                + ' - выбор позиций текущего пункта. Сделайте выбор: '))
                tn = int(str(op)[1])
                if not acc or acc > tn:
                    continue
                elif acc == tn:
                    svaiaO = op
                    break
                else:
                    svaiaO = cat7_4.operators[ii - (tn - acc)] 
                    break
        elif deep == 4:
            if str(op)[2] == '1':
                print()
                print(cat7_4.data[ii][0])
                print(cat7_4.data[ii][1])
            tn = int(str(op)[2])
            print(cat7_4.data[ii][2], '=', str(op)[2])
            if str(op)[3] == '0':
                acc = int(input('0 - перейти к следующему пункту от 1 ' + str(op)[2])
                                + 'до 3 - выбор позиции текущего пункта. Сделайте выбор: ')
                if not acc or acc > tn:
                    continue
                elif acc == tn:
                    svaiaO = op
                    break
                else:
                    svaiaO = cat7_4.operators[ii - (tn - acc)]
                    break
    print()
    
    # Расчёт сваи:
    print('Расчёт сваи')
    Gamma_C = 1 # Вычислять в последствии
    G =10  # 10 или 9.80665

    # svaiaС = int(input('0 - расчёт длины или 1 - подбор длины сваи? Сделайте выбор: '))
    if svaiaС:
        svaiaFT = int(input('Подбор по полной несущей способности сваи - 0 или только по боковой поверхности - 1 ?: '))
        print('Выборана несущая способность только по боковой поверхности' if svaiaFT 
                else 'Выборана полная несущая способность')
        svaiaF = float(input('Введите желаемую несущую способность (тонн): '))
        svaiaF *= G
        LPile = svaiaL
        while True:
            Fdse = CalcPile(Gamma_C, LPile, svaiaS, svaiaP, svaiaO, KN, hNoCalc)
            if type(Fdse) == int:
                raise ValueError("Ошибка расчёта или интерполяции; code = " + str(Fdse))
            ss = ''
            if svaiaFT:
                ss = 'несущая способность боковой поверхности:'
            else:
                ss = 'полная несущая способность сваи:'
            if Fdse[svaiaFT] <= svaiaF:
                print('Недостаточная длина сваи:', LPile, ss, round(Fdse[svaiaFT] / G, 2), 'тонн')
                LPile += 0.5
                if hlayers <= LPile:
                    print('Сведений по слоям грунта не хватает для увеличения длины сваи. Подбор прекращён.')
                    break
                continue
            else:
                if abs(Fdse[svaiaFT] - svaiaF)/svaiaF > 0.05:
                    print('Избыточная длина сваи:', LPile, ss, round(Fdse[svaiaFT] / G, 2), 'тонн')
                    LPile -= 0.2
                    if LPile < 3:
                        print('Свая не может быть уменьшена. Придел расчётов 3м. Подбор прекращён.')
                        break
                    continue
                else:
                    print()
                    print('Расчёт закончен! Fd =', round(Fdse[0], 2), ' kH', '(', round(Fdse[0] / G, 2), ') тонн')
                    print('Искомая длина сваи:', LPile, 'метров')
                    print('Несущая способность грунта под нижним концом сваи =', round(Fdse[2] / G, 2), 'тонн')
                    print('Несущая способность грунта по боковой поверхности сваи =', round(Fdse[1] / G, 2), 'тонн')
                    print('Предельно допустимая нагрузка =', round(Fdse[3] / G, 2), 'тонн')
                    break
    else:
        Fdse = CalcPile(Gamma_C, svaiaL, svaiaS, svaiaP, svaiaO, KN, hNoCalc)
        if type(Fdse) == int:
            raise ValueError("Ошибка расчёта или интерполяции; code = " + str(Fdse))
        print()
        print('Расчёт закончен! Fd =', round(Fdse[0], 2), ' kH', '(', round(Fdse[0] / G, 2), ') тонн')
        print('Несущая способность грунта под нижним концом сваи =', round(Fdse[2] / G, 2), 'тонн')
        print('Несущая способность грунта по боковой поверхности сваи =', round(Fdse[1] / G, 2), 'тонн')
        print('Предельно допустимая нагрузка =', round(Fdse[3] / G, 2), 'тонн')