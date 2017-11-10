import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class VHbbProducer(Module):
    def __init__(self):
        pass
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("Vtype",  "I");
        self.out.branch("Jet_lepFilter",  "O", 1, "nJet");
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        jets = Collection(event, "Jet")

        Vtype = -1

        wElectrons = [x for x in electrons if x.mvaSpring16GP_WP80 and x.pt > 25 and x.pfRelIso03_all < 0.12]      
        wMuons = [x for x in muons if x.pt > 25 and x.tightId >= 1 and x.pfRelIso04_all < 0.15]
        zElectrons = [x for x in electrons if x.pt > 20 and x.mvaSpring16GP_WP90 and x.pfRelIso03_all < 0.15]
        zMuons = [x for x in muons if x.pt > 20 and x.pfRelIso04_all < 0.25] # muons already preselected with looseId requirement

        zMuons.sort(key=lambda x:x.pt,reverse=True)
        zElectrons.sort(key=lambda x:x.pt,reverse=True)
        if len(zMuons) >= 2:
            if zMuons[0].pt > 20:
                for i in xrange(1,len(zMuons)):
                    if zMuons[0].charge * zMuons[i].charge < 0:
                        Vtype = 0
                        break
        elif len(zElectrons) >= 2:
            if zElectrons[0].pt > 20:
                for i in xrange(1,len(zElectrons)):
                    if zElectrons[0].charge * zElectrons[i].charge < 0:
                        Vtype = 1
                        break
        elif len(wElectrons) + len(wMuons) == 1:
            if len(wMuons) == 1:
                Vtype = 2
            if len(wElectrons) == 1:
                Vtype=3
        elif len(zElectrons) + len(zMuons) > 0:
            Vtype = 5
        else:
            Vtype = 4
            if event.__getattr__("MET_pt") < 150:
                Vtype = -1
       
        self.out.fillBranch("Vtype",Vtype)

        self.out.fillBranch("Jet_lepFilter",self.cleanJets(jets,electrons,muons))
 
        return True

    def cleanJets(self,jets,electrons,muons):
        # flag jets which overlap with loose electron or muon
        jetFlags = [] # bool whether to flag each jet in jets
        for jet in jets:
            overlap_muons = []
            overlap_electrons = []
            nMuons = jet.nMuons
            nElectrons = jet.nElectrons
            passFilter = True # if false then jet overlaps well loose muon or electron
            if nMuons > 0:
                overlap_muons.append(muons[jet.muonIdx1])
            if nMuons > 1:
                overlap_muons.append(muons[jet.muonIdx2])
            if nElectrons > 0:
                overlap_electrons.append(electrons[jet.electronIdx1])
            if nElectrons > 1:
                overlap_electrons.append(electrons[jet.electronIdx2])
            for muon in overlap_muons:
                if muon.pfRelIso04_all < 0.25 and muon.pt > 15:
                    passFilter = False
                    break
            if passFilter: # only check electrons if not already flagged from muons
                for electron in overlap_electrons:
                    if electron.pfRelIso03_all < 0.15 and electron.mvaSpring16GP_WP90 and electron.pt > 15:
                        passFilter = False
                        break
            jetFlags.append(passFilter)
        return jetFlags
                   
                

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

vhbb = lambda : VHbbProducer() 
