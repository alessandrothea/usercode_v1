#!/bin/env python

import ROOT
import uuid
import sys
import copy

class StyleSetter:
    _setters = {
        ROOT.TAttAxis:[ 
            ('labelfamily' , ROOT.TAxis.SetLabelFont), 
            ('labelsize'   , ROOT.TAxis.SetLabelSize), 
            ('labeloffset' , ROOT.TAxis.SetLabelOffset), 
            ('titlefamily' , ROOT.TAxis.SetTitleFont), 
            ('titlesize'   , ROOT.TAxis.SetTitleSize), 
            ('titleoffset' , ROOT.TAxis.SetTitleOffset), 
            ('ticklength'  , ROOT.TAxis.SetTickLength), 
            ('ndivisions'  , ROOT.TAxis.SetNdivisions), 
        ],

        ROOT.TAttText:[
            ('textfamily',ROOT.TAttText.SetTextFont),
            ('textsize'  ,ROOT.TAttText.SetTextSize),
            ('textcolor' ,ROOT.TAttText.SetTextColor),
            ('textangle' ,ROOT.TAttText.SetTextAngle),
            ('textalign' ,ROOT.TAttText.SetTextAlign),
        ],

        ROOT.TAttLine:[
            ('linecolor' ,ROOT.TAttLine.SetLineColor),
            ('linestyle' ,ROOT.TAttLine.SetLineStyle),
            ('linewidth' ,ROOT.TAttLine.SetLineWidth),
        ],

        ROOT.TAttFill:[
            ('fillcolor' ,ROOT.TAttFill.SetFillColor),
            ('fillstyle' ,ROOT.TAttFill.SetFillStyle),
            ('fillstyle' ,ROOT.TAttFill.SetFillStyle),
        ],
    }

    def __init__(self, **opts ):
        self._opts = opts

    def apply(self, tobj, **opts):

        myopts = self._opts.copy()
        myopts.update( opts )
        
        for cls,methods in self._setters.iteritems():
            if not isinstance(tobj,cls): continue

            for l,m in methods:
                x = myopts.get(l,None)
                if not x is None: m(tobj,x)

class Pad(object):

    _axisstyle = {
        'labelfamily' : 44,
        'labelsize'   : 20,
        'labeloffset' : 2,
        'titlefamily' : 44,
        'titlesize'   : 25,
        'titleoffset' : 30.,
        'ticklength'  : 10,
        'ndivisions'  : 505,
    }
    #---
    def __init__(self, name, width=500, height=500, **opts ):
        self._name = name
        self._w = width
        self._h = height
        self._align = ('c','m') # lcr
        self._showtitle = False
        self._showstats = False
        self._obj = None

        self._margins = (60,60,60,60)
        self._xaxis = self._axisstyle.copy()
        self._yaxis = self._axisstyle.copy()
    
        # temp solution

        for n,o in opts.iteritems():
            attr = '_'+n
            if not hasattr(self,attr): continue
            if n == 'xaxis' or n == 'yaxis':
                getattr(self,attr).update(o)
            else:
                setattr(self,attr,o)
        self._build()

    #---
    def _build(self):
        m = self._margins
        if isinstance(m,tuple):
            if len(m) == 1:
                m = (m[0],m[0],m[0],m[0])
            elif len(m) == 2:
                m = (m[0],m[0],m[1],m[1])
            elif len(m) == 4:
                pass
            else:
                raise ValueError('margins must be a 1,2,4 length tuple')
        self._margins = m

    def __str__(self):
        return '%s(\'%s\',w=%d,h=%d,obj=%s)' % (self.__class__.__name__,self._name,self._w,self._h,self._obj)

    #---
    def __getattr__(self,name):
        if not self._obj:
            raise AttributeError('%s not found' % name)
        return getattr(self._obj,name)


    #---
    def _applypadstyle(self):

        left,right,top,bottom = self._margins
        fh,fw = float(self._h),float(self._w)

        if not top    is None : self._obj.SetTopMargin    ( top/fh )
        if not bottom is None : self._obj.SetBottomMargin ( bottom/fh )
        if not left   is None : self._obj.SetLeftMargin   ( left/fw )
        if not right  is None : self._obj.SetRightMargin  ( right/fw )

    #---
    def _applyframestyle(self):

        h = None
        for o in self._obj.GetListOfPrimitives():
            if not (isinstance(o,ROOT.TH1) or isinstance(o,ROOT.THStack) or isinstance(o,ROOT.TMultiGraph)): continue
            h = o
            break

        if not h: return

        if not self._showtitle:
            frame = h.GetHistogram() if isinstance(h, ROOT.THStack) or isinstance(h,ROOT.TMultiGraph) else h
            frame.SetBit(ROOT.TH1.kNoTitle)

            for o in self._obj.GetListOfPrimitives():
                if isinstance(o,ROOT.TPaveText) and o.GetName()=='title':
                    ROOT.SetOwnership(o,True)
                    del o

        if not self._showstats:
            frame.SetBit(ROOT.TH1.kNoStats)
            o = h.FindObject('stats')
            if o.__nonzero__():
                ROOT.SetOwnership(o,True)
                del o
        
        left,right,top,bottom = self._margins
        lax = self._w-left-right
        lay = self._h-top-bottom

        setter = StyleSetter()

        xax = h.GetXaxis()
        style = self._xaxis.copy()
        style['ticklength']  *= self._w/float(lax*self._h)
        style['labeloffset'] /= float(self._h-top-bottom)
        style['titleoffset'] *= self._obj.GetWh()/(1.6*self._h*style['titlesize'])
        setter.apply(xax,**style)

        yax = h.GetYaxis()
        style = self._yaxis.copy()
        style['ticklength']  *= self._h/float(lay*self._w)
        style['labeloffset'] /= float(self._w-left-right)
        style['titleoffset'] *= self._obj.GetWh()/(1.6*self._w*style['titlesize'])
        setter.apply(yax,**style)


class Canvas(object):
    _log = None

    #---
    def __init__(self, nx, ny):
        self._nx = nx
        self._ny = ny
        self._pads = []
        self._grid = [[None]*ny for i in xrange(nx)]
        self._hrows = [0.]*nx
        self._wcols = [0.]*ny
        self._obj = None

    
    #---
    def __getattr__(self,name):
        if not self._obj:
            raise AttributeError
        return getattr(self._obj,name)

    # the alignement should be decided here
    def attach(self, pad, i, j ):
        if ( i < 0 and i > self._nx ) or ( j < 0 and j > self._ny ):
            raise IndexError('Index out of bounds (%d,%d) not in [0,%d],[0,%d]' % (i,j,self._nx,self._ny))

        self._grid[i][j] = pad
        self._pads.append(pad)
#         print 'attach',i,j
#         print self._grid

    def __setitem__(self,key,value):
        if not isinstance(key,tuple):
            raise TypeError('XXXX')

        if len(key) != 2:
            raise RuntimeError('Wrong dimension')
        
        self.attach( value, *key )

    #---
    def get(self,i,j):
        return self._grid[i][j]

    #---
    def __getitem__(self, key):
        if not isinstance(key,tuple):
            raise TypeError('XXXX')

        if len(key) != 2:
            raise RuntimeError('Wrong dimension')
        
        return self.get( *key )

    #---
    def _computesize(self):
        
        hrows = [0]*self._ny
        wcols = [0]*self._nx

        for i,col in enumerate(self._grid):
            wcols[i] = max([(pad._w if pad else 0) for pad in col])
            for j,pad in enumerate(col):
                if not pad: continue
                hrows[j] = max(hrows[j],pad._h)

        
        self._hrows = hrows
        self._wcols = wcols
        h = sum(self._hrows)
        w = sum(self._wcols)

        return w,h

    #---
    def _getanchors(self,i,j):
        return sum(self._wcols[0:i]),sum(self._hrows[0:j])

    #---
    def makecanvas(self, name=None, title=None):

        if not name : name = 'canvas_'+str(uuid.uuid1())
        if not title: title = name

        w,h = self._computesize()
        fw,fh = float(w),float(h)
        c = ROOT.TCanvas(name,title, w+4, h+28)
        c.Draw()

        k = 2
        
        # loop over rows (y-index j)

        for i,col in enumerate(self._grid):
            # loop over columns (x-index i)
            for j,pad in enumerate(col):
                if not pad: continue

                # assule left-top alignement
                x0,y0 = self._getanchors(i,j)
                x1,y1 = x0+pad._w,y0+pad._h

                gw,gh = self._wcols[i],self._hrows[j]
#                 print i,j,gw,gh,pad._w,pad._h

                ha,va = pad._align
                
                if   va == 't':
                    pass
                elif va == 'm':
                    y0 += (gh-pad._h)/2.
                    y1 += (gh-pad._h)/2.
                elif va == 'b':
                    y0 += gh-pad._h
                    y1 += gh-pad._h
                else:
                    raise KeyError('Unknown vertical alignement %s', va)

                if   ha == 'l':
                    pass
                elif ha == 'c':
                    x0 += (gw-pad._w)/2.
                    x1 += (gw-pad._w)/2.
                elif ha == 'r':
                    x0 += gw-pad._w  
                    x1 += gw-pad._w
                else:
                    raise KeyError('Unknown horizontal alignement %s', ha)

                pname = 'pad_%d_%d' % (i,j)

#                 print pname,' [%d,%d][%d,%d] - [%d,%d][%d,%d]'% (x0,x1,y0,y1,x0,x1,(h-y1),(h-y0)), k
#                 print pname,x0/fw,(h-y0)/fh,x1/fw,(h-y1)/fh, k
                tpad = ROOT.TPad(pname,pname,x0/fw,(h-y1)/fh,x1/fw,(h-y0)/fh)#, k)
                tpad.Draw()
                pad._obj = tpad
                pad._applypadstyle()
                k += 1
        
        self._obj = c
        return c
        
    #---
    def applystyle(self):
        
        map(Pad._applyframestyle,self._pads)


class Legend(object):

    _legendstyle = {
        'textfamily' : 44,
        'textsize'   : 20,
        'textcolor'  : ROOT.kBlack,
    }

    #---
    def __init__(self, nx, ny, labelwidth, boxsize, **opts):
        self._labelwidth = labelwidth 
        self._boxsize = boxsize
        self._nx = nx
        self._ny = ny

        self._anchor = (0,0)
        self._align = ('c','m')
        self._style = self._legendstyle.copy() 

        for n,o in opts.iteritems():
            attr = '_'+n
            if not hasattr(self,attr): continue
            setattr(self,attr,o)

        self._grid = [[None]*ny for i in xrange(nx)]
        self._legends = []
        self._sequence = [ (i,j) for i in xrange(self._nx) for j in xrange(self._ny) ]
        self._index = 0

    #---
    @property
    def sequence(self):
        return self._sequence[:]

    @sequence.setter
    def sequence(self,value):

        if len(set(value)) != len(value):
            raise RuntimeError('There are duplicates in the new sequence!')

        if len(value) > self._nx*self._ny:
            raise ValueError('New sequence longer than label')

        self._sequence = value


    #---
    def _getanchor(self,i,j):
        return (self._anchor[0]+i*self._labelwidth,self._anchor[1]+j*self._boxsize)

    #---
    def _applystyle(self,leg):
        leg.SetFillStyle(0)
        leg.SetBorderSize(0)
        leg.SetMargin( 1 )

        methods = [
            ('textfamily'      , leg.SetTextFont),
            ('textsize'        , leg.SetTextSize),
        ]

        for l,m in methods:
            x = self._style.get(l,None)
            if not x is None: m(x)#; print x,m.__name__


    #---
    def addentry(self, obj, opt='', title=None, pos=None ):
        # override the appendion sequence
        if pos:
            i,j = pos
            if ( i < 0 and i > self._nx ) or ( j < 0 and j > self._ny ):
                raise IndexError('Index out of bounds (%d,%d) not in [0,%d],[0,%d]' % (i,j,self._nx,self._ny))
        else:
            if self._index >= len(self._sequence):
                raise IndexError('The legend is full!')
            
            i,j = self._sequence[self._index]

            self._index += 1

        if not self._grid[i][j] is None:
            raise RuntimeError('Entry (%d,%d) is already assigned' % (i,j))

        self._grid[i][j] = (obj,opt,title)


    #---
    def draw(self):
        
        pad = ROOT.gPad.func()
        fw = pad.GetWw()*pad.GetWNDC()
        fh = pad.GetWh()*pad.GetHNDC()

        for i,col in enumerate(self._grid):
            for j,entry in enumerate(col):
                if not entry: continue
                obj,opt,title = entry

                x0,y0 = self._getanchor(i,j)
                x1,y1 = x0+self._boxsize,y0+self._boxsize
                ratio = float(self._boxsize)/float(self._labelwidth)

                l = ROOT.TLegend( x0/fw, (fh-y1)/fh, x1/fw, (fh-y0)/fh )
                l.AddEntry(obj,obj.GetTitle() if title is None else title,opt)
                self._applystyle(l)
                l.Draw()
                self._legends.append(l)

class Latex:
    _latexstyle = {
            'textfamily':44,
            'textsize'  :20,
            'textcolor' :ROOT.kBlack,
        }
    _hcodes = {
        'l':10,
        'c':20,
        'r':30,
    }
    _vcodes = {
        'b':1,
        'm':2,
        't':3,
    }


    # ---
    def __init__(self,text,**opts):
        self._text   = text

        self._anchor = (0,0)
        self._align = ('c','m')
        self._style = self._latexstyle.copy()

        for n,o in opts.iteritems():
            attr = '_'+n
            if not hasattr(self,attr): continue
            if n == 'style':
                getattr(self,attr).update(o)
            else:
                setattr(self,attr,o)

        self._latex = ROOT.TLatex()
        self._latex.SetNDC()


    # ---
    def draw(self):

        pad = ROOT.gPad.func()
        fw = float(pad.GetWw()*pad.GetWNDC())
        fh = float(pad.GetWh()*pad.GetHNDC())

        ha,va = self._align
        self._latex.SetTextAlign(self._hcodes[ha]+self._vcodes[va])

        setter = StyleSetter(**self._style)
        setter.apply(self._latex)

        x0,y0 = self._anchor
        print x0,y0
        self._latex.SetText( x0/fw, 1-(y0/fh), self._text )

        self._latex.Draw()


if __name__ == '__main__':

    sys.argv.append('-b')
    ROOT.gROOT.SetBatch()
    
    c = Canvas(2,3)

    axst = {
    'labelfamily'       : 44,
    'labelsize'         : 20,
    'labeloffset'       : 0,
    'titlefamily'       : 44,
    'titlesize'         : 20,
    'titleoffset'       : 50,
    'ticklength'        : 10
    }
#     axst = {'label-family':42, 'label-size':0.04, }

    p0 = Pad('p0',200,500, margins=(20,80,80,20), xaxis = axst, yaxis = axst, align=('l','b')  )
    p1 = Pad('p1',500,500, margins=(80,20,20,20), xaxis = axst, yaxis = axst )
    p2 = Pad('p2',500,200, margins=(80,20,20,20), xaxis = axst, yaxis = axst )
    p3 = Pad('p3',500,200, margins=(80,20,20,80), xaxis = axst, yaxis = axst )
    p4 = Pad('p4',200,200, margins=(20,80,20,80), xaxis = axst, yaxis = axst )
    p5 = Pad('p5',200,200, margins=(20,80,80,20), xaxis = axst, yaxis = axst, align=('l','b') )
    p1._xaxis['label-size'] = 0.0
    p2._xaxis['label-size'] = 0.0
#     p3._xaxis['title-offset'] = 2.5
#     p4._xaxis['title-offset'] = 2.5

#     c.attach(p0,1,0)
    c[1,0] = p0
    c.attach(p1,0,0)
    c.attach(p2,0,1)
    c.attach(p3,0,2)
    c.attach(p4,1,2)
    c.attach(p5,1,1)


    tc = c.makecanvas()
    tc.SetName('aaa')

    print c[1,0]

    bins = 10
    hdummy = ROOT.TH1F('dummy','',bins,0,bins)
    hs = ROOT.THStack('stack','stocazz')
    hcols = []
    for i in xrange(bins):
        h = hdummy.Clone('col%d' % i)
        h.SetTitle(h.GetName())
        h.SetFillColor(i+ROOT.kOrange)
        h.SetLineColor(i+ROOT.kOrange)
        h.SetFillStyle(3001)
        h.SetLineWidth(2)
        h.Fill(i,i)
        ROOT.SetOwnership(h,False)
        hs.Add(h)
        hcols.append(h)


    p1.cd()
    hs1 = hs.Clone('xxx')
    hs1.Draw()
    hs1.GetYaxis().SetTitle('y-axis')
    hs1.GetXaxis().SetTitle('x-axis')
#     hs.Draw()
    leg = Legend(4,4, 80,30, anchor=(90,30))
    sequence = leg.sequence
    sequence.remove( (1,3) )
    sequence.remove( (2,3) )
    sequence.remove( (2,2) )
    leg.sequence = sequence
    leg.addentry(hcols[0],'f')
    leg.addentry(hcols[1],'f')
    leg.addentry(hcols[2],'f')
    leg.addentry(hcols[3],'f')
    leg.addentry(hcols[4],'f')
    leg.addentry(hcols[5],'f')
    leg.addentry(hcols[6],'f')
    leg.addentry(hcols[7],'f')
    leg.addentry(hcols[8],'f')
    leg.addentry(hcols[9],'f')
    leg.draw()

    p2.cd()
    hs2 = hs.Clone('yyy')
    hs2.Draw()
    hs2.GetYaxis().SetTitle('y-axis')
#     hs.Draw()

    pad = c.get(0,2)
    pad.cd()
    d3 = hdummy.Clone('d3')
    d3.GetYaxis().SetTitle('y-axis')
    d3.GetXaxis().SetTitle('x-axis')
    d3.Draw()

    pad = c.get(1,2)
    pad.cd()
    d4 = hdummy.Clone('d4')
    d4.GetXaxis().SetTitle('x-axis')
    d4.Draw('Y+')

    pad = c.get(1,1)
    pad.cd()
    d5 = hdummy.Clone('d5')
    d5.GetXaxis().SetTitle('x-axis')
    d5.Draw('Y+')

#     p0.cd()
#     d0 = hdummy.Clone('d0')
#     d0.GetXaxis().SetTitle('x-axis')
#     d0.Draw('Y+')

    c.applystyle()

#     tc.ls()
    ROOT.gSystem.ProcessEvents()
    

#     tc.Print('des.png')
    tc.Print('des.pdf')
    tc.Print('des.root')



        