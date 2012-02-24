#!/usr/bin/env python


import sys
import ROOT
import optparse
import hwwinfo
import os.path
import string
import logging
from HWWAnalysis.Misc.odict import OrderedDict

class ShapeFactory:
    def __init__(self):
        self._baseWgt = 'baseW*puW*effW*triggW'

        ranges = {}
        ranges['bdtl']       = (400  , -1. , 1.)
        ranges['bdts']       = (400  , -1. , 1.)
        ranges["mth"]        = (400  , 0   , 200)
        ranges["dphill"]     = (400  , 0   , 3.15)
#         ranges["gammaMRStar"]= (1200 , 0   , 600)
        self._ranges = ranges
        
        self._dataTag = '2011A'
        self._masses = []
        self._jets = []
        self._channels = []
        # paths (to move out)
        self._outFileFmt  = ''
        self._paths = {}

    def __del__(self):
        pass
    
    def getrange(self,var,mass,njet):
        
        if var=='mll':
#             return (600  , 0   , 600)
            return self._getmllrange(mass,njet)

        if var == 'gammaMRStar':
            return self._getGMstarrange(mass,njet)

        varRange = self._ranges[var]
        if isinstance(varRange,tuple):
            return varRange
        elif isinstance(varRange,dict):
            return varRange[mass][njet]
            
    def _getmllrange(self,mass,njet):
        
        # TODO: cleanup


#         xmin = 10.
#         xmax = hwwinfo.singleVarCuts['mllmax_bdt'][mass]
#         bins = 200 if njet == 0 else 200
#         
#         return (bins,xmin,xmax)


        # xmin
        xmin   = 0. if mass<300 else 0.2*mass-20      #;--> changed "(mH<300)" and "0.2*float(mH) - 20"
        # xmax
        if mass < 200.:
            xmax = 200.
        elif mass < 400.:
            xmax = mass
        else:
            xmax = mass-50.
        # bins
        if mass < 300.:
            bins = 400 if njet == 0 else 200
        else:
            bins = 300 if njet == 0 else 150
        return (bins,xmin,xmax)
    
    def _getGMstarrange(self,mass,njet):
        # lower alwyas 50
        # upper 100+(mH-100)*0.5
        xmin=40
        xmax=90.+(mass-100.)*0.6

        if njet ==1: xmax += 20

        if mass < 300.:
            bins = 200 if njet == 0 else 200
        else:
            bins = 150 if njet == 0 else 150
        return (bins,xmin,xmax)


    def makeNominals(self, var, sel, inputDir, outPath, **kwargs):
        
        ROOT.TH1.SetDefaultSumw2(True)

        shapeFiles = []
        # mass dependent sample list, can be in the mass loop
        for mass in self._masses:
            samples = hwwinfo.samples(mass, self._dataTag)
            # mass and variable selection
            allCuts = hwwinfo.massSelections( mass )
            varSelection = allCuts[sel+'-sel']
            varCtrlZ     = allCuts[sel+'-ctrZ']
            
            #inner  jet and channel loops
            for njet in self._jets:
                for channel in self._channels:
                    pars = dict([
                        ('mass',mass),
                        ('jets',njet),
                        ('channel',channel)
                    ])
                    print '-'*80
                    print ' Processing: mass',mass,'jets',njet,'channel',channel
                    print '-'*80
                    
                    # ----
                    activeInputPaths = ['base']
                    if var in self._paths: activeInputPaths.append(var)

                    dirmap = {}
                    for path in activeInputPaths:
                        dirmap[path]=(self._paths[path]+'/'+inputDir).format( **pars )

                    print 'Input dir:',dirmap.values()

                    inputs = self._connectInputs(var,samples, dirmap)
                    
                    # and the output path (might be par dependent as well)
                    output = outPath.format(**pars)
                    outdir = os.path.dirname(output)
                    if outdir:
                        self._ensuredir(outdir)

                    print '.'*80
                    print 'Output file:',output

                    # now build the selection
                    jetSel = 'njet == {0}'.format(njet)
                    selection = varSelection+' && '+jetSel+' && '+hwwinfo.channelCuts[channel]
                    selections = dict(zip(samples.keys(),[selection]*len(samples)))
                    dyshapes = ['DYLLtemplate','DYLLtemplatesyst']
                    for n in dyshapes:
#                         if n in selections:
                        selections[n] = varCtrlZ+' && '+jetSel+' && '+hwwinfo.channelCuts[channel]

                    self._addweights(mass,var,selections)

                    print '.'*80
                    rng = self.getrange(var,mass,njet) 
                    self._draw(var, rng, selections ,output,inputs)
                    self._disconnectInputs(inputs)
                    shapeFiles.append(output)
        return shapeFiles

    def makeSystematics(self,var,sel,syst,mask,inputDir,outPath,**kwargs):
        ROOT.TH1.SetDefaultSumw2(True)
        shapeFiles = []
        nicks = kwargs['nicks'] if 'nicks' in kwargs else None
        # mass dependent sample list, can be in the mass loop
        for mass in self._masses:
            samples = hwwinfo.samples(mass, self._dataTag)
            # mass and variable selection
            allCuts = hwwinfo.massSelections( mass )
            varSelection = allCuts[sel+'-sel']
            
            #inner  jet and channel loops
            for njet in self._jets:
                for channel in self._channels:
                    print '-'*80
                    print ' Processing: mass',mass,'jets',njet,'channel',channel
                    print '-'*80

                    pars = dict([
                        ('mass',mass),
                        ('jets',njet),
                        ('channel',channel),
                        ('syst',syst),
                    ])
                    pars['nick'] = nicks[syst] if nicks else syst

                    # ----
                    activeInputPaths = ['base']
                    if var in self._paths: activeInputPaths.append(var)

                    dirmap = {}
                    for path in activeInputPaths:
                        dirmap[path]=(self._paths[path]+'/'+inputDir).format( **pars )

                    inputs = self._connectInputs(var,samples, dirmap, mask)

                    # ---

                    # and the output path (might be par dependent as well)
                    output = outPath.format(**pars)
                    outdir = os.path.dirname(output)
                    if output:
                        self._ensuredir(outdir)
                    print '.'*80
                    print 'Output file',output

                    # now build the selection
                    jetSel = 'njet == {0}'.format(njet) #njet>%.1f && njet<%.1f' % (njet-0.5,njet+0.5)
                    selection = varSelection+' && '+jetSel+' && '+hwwinfo.channelCuts[channel]
                    selections = dict(zip(samples.keys(),[selection]*len(samples)))
#                     print selections
                    self._addweights(mass,var,selections)

                    print '.'*80
                    rng = self.getrange(var,mass,njet) 
                    self._draw(var, rng, selections ,output,inputs)
                    self._disconnectInputs(inputs)
                shapeFiles.append(output)
        return shapeFiles
    
    def _draw(self, var, rng, selections, output, inputs):
        '''
        var :       the variable to plot
        selection : the selction to draw
        output :    the output file path
        inputs :    the process-input files map
        '''
        logging.info('Yields by process')
        outFile = ROOT.TFile.Open(output,'recreate')
        for process,tree  in inputs.iteritems():
            print ' '*3,process.ljust(20),':',tree.GetEntries(),
            # new histogram
            shapeName = 'histo_'+process
            shape = ROOT.TH1D(shapeName,process+';'+var,
                              rng[0],
                              rng[1],
                              rng[2]
                             )
            outFile.cd()

            cut = selections[process]

            logging.debug('Applied cut: '+cut)
            entries = tree.Draw( var+'>>'+shapeName, cut, 'goff')
            print ' >> ',entries
            shape.Write()
        outFile.Close()
        del outFile

    # add the weights to the selection
    def _addweights(self,mass,var,selections):
        sampleWgts =  self._sampleWeights(mass,var)
        print '--',selections.keys()
        for process,cut in selections.iteritems():
            wgt = self._baseWgt
            if process in sampleWgts:
                wgt += '*'+sampleWgts[process]

            selections[process] = wgt+'*('+cut+')'

    # this is too convoluted
    # define here the mass-dependent weights
    def _sampleWeights(self,mass,var):
        weights = {}
        weights['ggH']          = 'kfW'
        weights['ggH-SI']       = 'kfW'
        weights['WJet']         = 'fake2W'
        weights['WJetFakeRate'] = 'fake2W'
        weights['Data']         = '1'
        weights['Vg']           = '(1+0.55*(dataset == 85||dataset == 86))' #TODO move to mkMerged, read from external scale factor file
        
        stupidmasses = [118, 122, 124, 126, 128, 135]
        if var in ['bdts','bdtl'] and mass in stupidmasses:
            weights['ggH']+='*2*(event%2==0)'
            weights['vbfH']='2*(event%2==0)'
            weights['wzttH']='2*(event%2==0)'
            # TODO Signal injection weights, if available
            weights['ggH-SI']+='*2*(event%2==0)'
            weights['vbfH-SI']='2*(event%2==0)'
            weights['wzttH-SI']='2*(event%2==0)'
            
        return weights
#         sys.exit(0)

    def _ensuredir(self,directory):
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                if e.errno == 17:
                    pass
                else:
                    raise e

    def _connectInputs(self, var, samples, dirmap, mask=None):
        inputs = {}
        treeName = 'latino'
        for process,filenames in samples.iteritems():
            if mask and process not in mask:
                continue
            tree = self._buildchain(treeName,[ (dirmap['base']+'/'+f) for f in filenames])
            if 'bdt' in var:
                bdttreeName = 'latinobdt'
                bdtdir = self._paths[var]
                bdttree = self._buildchain(bdttreeName,[ (dirmap[var]+'/'+f) for f in filenames])
                
                if tree.GetEntries() != bdttree.GetEntries():
                    raise RuntimeError('Mismatching number of entries: '+tree.GetName()+'('+str(tree.GetEntries())+'), '+bdttree.GetName()+'('+str(bdttree.GetEntries())+')')
                print ' '*3,process.ljust(20),'- master: ',tree.GetEntries(), ' friend ', bdttree.GetEntries()
                tree.AddFriend(bdttree)

            inputs[process] = tree

        return inputs

    def _disconnectInputs(self,inputs):
        for n in inputs.keys():
            friends = inputs[n].GetListOfFriends()
            if friends.__nonzero__():
                for fe in friends:
                    friend = fe.GetTree()
                    inputs[n].RemoveFriend(friend)
                    ROOT.SetOwnership(friend,True)
                    del friend
            del inputs[n]
    
    def _buildchain(self,treeName,files):
        tree = ROOT.TChain(treeName)
        for path in files:
            logging.debug('     '+str(os.path.exists(path))+' '+path)
            if not os.path.exists(path):
                raise RuntimeError('File '+path+' doesn\'t exists')
            tree.Add(path) 

        return tree

    

if __name__ == '__main__':
#     logging.basicConfig(level=logging.DEBUG)
    
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)

    parser.add_option('--sel',            dest='sel',           help='selection cut',                         default=None)
    parser.add_option('--dataset',        dest='dataset',       help='dataset to process',                    default=None)
    parser.add_option('--path_latino',    dest='path_latino',   help='Root of the master trees',              default=None)
    parser.add_option('--path_bdt',       dest='path_bdt',      help='Root of the friendly bdt trees',        default=None)
    parser.add_option('--path_shape_raw', dest='path_shape_raw',   help='destination directory of nominals',     default=None)

    parser.add_option('--noNoms',       dest='makeNoms',    help='Do not produce the nominal',            action='store_false',   default=True)
    parser.add_option('--noSyst',       dest='makeSyst',    help='Do not produce the systematics',        action='store_false',   default=True)
    parser.add_option('--doSyst',       dest='doSyst',      help='Do only one systematic',                default=None)
    hwwinfo.addOptions(parser)
    hwwinfo.loadOptDefaults(parser)
    (opt, args) = parser.parse_args()

    sys.argv.append( '-b' )
    ROOT.gROOT.SetBatch()

    if not opt.dataset:
        parser.print_help()
        parser.error('Dataset not defined')

    if not opt.sel:
        parser.print_help()
        parser.error('Selection not defined')

    if not opt.path_latino:
        parser.print_help()
        parser.error('Master tree path not defined')

    if not opt.path_shape_raw: 
        parser.print_help()
        parser.error('Where shall I put the shapes?')


    variable = opt.var
    selection = opt.sel

#     latinoDir           = '/shome/thea/HWW/ShapeAnalysis/trees/latino_skim'
#     bdtDir              = '/shome/thea/HWW/ShapeAnalysis/trees/bdt_skim/ntupleMVA_MH{mass}_njet{jets}'

    latinoDir           = opt.path_latino
    bdtDir              = opt.path_bdt
    nomOutDir           = os.path.join(opt.path_shape_raw,'nominals/')
    systOutDir          = os.path.join(opt.path_shape_raw,'systematics/')
    
    nomInputDir         = 'all/'
    systInputDir        = '{syst}/'

    nominalOutFile      = 'histo_H{mass}_{jets}jet_'+variable+'shapePreSel_{channel}.root'
    systematicsOutFile  = 'histo_H{mass}_{jets}jet_'+variable+'shapePreSel_{channel}_{nick}.root'
    
    factory = ShapeFactory()
    factory._outFileFmt  = nominalOutFile
#     factory._nominalDir  = '/scratch/maiko/postLP/MVA/ntupleMVA/ntupleMVA_MH{mass}_njet{jets}/'
#     factory._systematicsDir = '/scratch/maiko/postLP/MVA/' 

    masses = hwwinfo.masses[:] if opt.mass == 0 else [opt.mass]
    factory._masses   = masses
    factory._jets     = hwwinfo.jets[:]
    factory._channels = hwwinfo.channels[:]
    factory._paths['base']  = latinoDir
    factory._paths['bdtl']  = bdtDir
    factory._paths['bdts']  = bdtDir

#     print factory._masses
#     sys.exit(0) 

    factory._dataTag = opt.dataset    

    if opt.makeNoms:
        # nominal shapes
        print factory.makeNominals(variable,selection,nomInputDir,nomOutDir+nominalOutFile)

    if opt.makeSyst:
        # systematic shapes
        systematics = OrderedDict([
            ('electronResolution'    , 'p_res_e'),
            ('electronScale_down'    , 'p_scale_eDown'),
            ('electronScale_up'      , 'p_scale_eUp'),
            ('jetEnergyScale_down'   , 'p_scale_jDown'),
            ('jetEnergyScale_up'     , 'p_scale_jUp'),
            ('leptonEfficiency_down' , 'eff_lDown'),
            ('leptonEfficiency_up'   , 'eff_lUp'),
            ('metResolution'         , 'met'),
            ('muonScale_down'        , 'p_scale_mDown'),
            ('muonScale_up'          , 'p_scale_mUp'),
        ])

        mask = ['ggH', 'vbfH', 'ggWW', 'Top', 'WW', 'VV']
        systMasks = dict([(s,mask[:]) for s in systematics])

        for s,m in systMasks.iteritems():
            if opt.doSyst and opt.doSyst != s:
                continue
            print '-'*80
            print ' Processing',s,'for samples',' '.join(mask)
            print '-'*80
            files = factory.makeSystematics(variable,selection,s,m,systInputDir,systOutDir+systematicsOutFile, nicks=systematics)
    #         for old in files:
    #             new = old.replace(s,systematics[s])
    #             print 'Renaming',old,'->',new
    #             os.rename(old,new)
            
    print 'Used options'
    print ', '.join([ '{0} = {1}'.format(a,b) for a,b in opt.__dict__.iteritems()])