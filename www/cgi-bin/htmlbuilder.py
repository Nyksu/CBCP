# Библиотека работы с формирование HTML страниц.
# v 1.0.1 beta

class htmlpage:
    pages = {}
    csspath = ''

    def __init__(self, routname, toper, grounder, css):
        self.routname = routname
        self.toper = toper
        self.grounder = grounder
        self.css = css
        self.lines = []
        self.contentOnly = []
        self.lastotag = ''
        htmlpage.pages[routname] = self
    
    def addString(self, newtag, params, ss, needclosetag):
        if self.lastotag != '' and (needclosetag or newtag !=''):
            self.closetag()
        if newtag !='':
            self.lastotag = newtag
            parstr = ''
            if params != '':
                for par in params.keys():
                    parstr += ' {}="{}"'.format(str(par), params[par])
            self.lines.append('<{}{}>'.format(newtag, parstr))
        self.lines.append(ss)
        self.contentOnly.append(ss)
        if needclosetag and newtag !='':
            self.closetag()
    
    def closetag(self):
        if self.lastotag != '':
            self.lines.append('</{}>'.format(self.lastotag))
            self.lastotag = ''

    def printHTML(self):
        css = ''
        if self.css:
            css = '<link rel="stylesheet" href="{}">'.format(htmlpage.csspath)
        print(str(self.toper).format(cssstr = css))
        for ss in self.lines:
            print(ss)
        print(self.grounder)
    
    def addStringsData(self, data):
        for itm in data.Keys():
            if type(data[itm]) == list:
                # множественные данные (например слои грунта)
                for dd in data[itm]:
                    self.addStringsData(dd)
            elif type(data[itm]) == tuple:
                ss = '<p>{} <strong>{}</strong> {}</p>'.format(data[itm][2], str(data[itm][0]), data[itm][1])
                self.addString('', '', ss, False)
        
        