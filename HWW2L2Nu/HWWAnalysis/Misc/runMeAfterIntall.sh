echo $CMSSW_BASE
cd $CMSSW_BASE/src
addpkg PhysicsTools/PythonAnalysis 
addpkg PhysicsTools/Utilities V08-03-00
cvs co HiggsAnalysis/HiggsToWW2Leptons
