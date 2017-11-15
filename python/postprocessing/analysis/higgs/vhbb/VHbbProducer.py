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

        ## filter jets that overlap with any of the selected leptons
        allLeptons = zElectrons[:]
        allLeptons.extend(zMuons)
        allLeptons.extend(wElectrons)
        allLeptons.extend(wMuons)
        jetFilterFlags = [True]*len(jets)
        for lepton in allLeptons:
            jetInd = lepton.jetIdx
            if jetInd >= 0:
                jetFilterFlags[jetInd] = False

        self.out.fillBranch("Jet_lepFilter",jetFilterFlags)
 
        return True
                

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

vhbb = lambda : VHbbProducer() 
