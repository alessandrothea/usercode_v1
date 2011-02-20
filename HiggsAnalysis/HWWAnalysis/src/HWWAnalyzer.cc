/*
 * HWWAnalyzer.cc
 *
 *  Created on: Dec 14, 2010
 *      Author: ale
 */

#include "HWWAnalyzer.h"
#include <TChain.h>
#include <TFile.h>
#include <TVector3.h>
#include <TLorentzVector.h>
#include "Tools.h"
#include "HWWEvent.h"
#include "HWWNtuple.h"
#include <stdexcept>
#include <fstream>
#include <TH1F.h>
#include <TDatabasePDG.h>
#include <TParticlePDG.h>

//_____________________________________________________________________________
void HWWAnalyzer::HiggsCutSet::print() {
//	std::cout << hMass << '\t'
//			<< ll << '\t'
//			<< etaMax << '\t'
//			<< etaMaxHard << '\t'
//			<< etaMaxSoft << '\t'
//			<< metMin << '\t'
//			<< metMax << '\t'
//			<< invMassMax << '\t'
//			<< deltaPhi << '\t'
//			<< ptMaxMin << '\t'
//			<< ptMaxMax << '\t'
//			<< ptMinMax << std::endl;
		std::cout << hMass << '\t'
				<< minPtHard << '\t'
				<< minPtSoft << '\t'
				<< maxMll << '\t'
				<< maxDphi << '\t'
				<< std::endl;
}
//_____________________________________________________________________________
HWWAnalyzer::HWWAnalyzer(int argc, char** argv) : UserAnalyzer(argc,argv), _nthMask(kNumCuts),
		_analysisTree(0x0), _event(0x0), _ntuple(0x0) {
	// TODO Auto-generated constructor stub

	_analysisTreeName = _config.getValue<std::string>("HWWAnalyzer.analysisTreeName");
	_higgsMass        = _config.getValue<int>("HWWAnalyzer.higgsMass");

	_maxD0            = _config.getValue<float>("HWWAnalyzer.maxD0");
	_maxDz            = _config.getValue<float>("HWWAnalyzer.maxDz");
	_cutFile          = _config.getValue<std::string>("HWWAnalyzer.cutFile");
	_minMet           = _config.getValue<float>("HWWAnalyzer.minMet");
	_minMll           = _config.getValue<float>("HWWAnalyzer.minMll");
	_zVetoWidth       = _config.getValue<float>("HWWAnalyzer.zVetoWidth");

	_minProjMetEM     = _config.getValue<float>("HWWAnalyzer.minProjMetEM");
	_minProjMetLL     = _config.getValue<float>("HWWAnalyzer.minProjMetLL");


	TDatabasePDG* pdg = TDatabasePDG::Instance();
	_Z0 = pdg->GetParticle("Z0");

	readHiggsCutSet( _cutFile );

//	_eeCuts = getHiggsCutSet( _higgsMass, kEE );
//	_mmCuts = getHiggsCutSet( _higgsMass, kMM );
//	_emCuts = getHiggsCutSet( _higgsMass, kEM );

	_theCuts = getHiggsCutSet( _higgsMass );

	// initialize the bitmask
	higgsBitWord dummy( (1 << kNumCuts )-1);
	dummy.set(0,0).set(1,0);
	_theMask = dummy;

	// initialize the n-1 masks
	for( int k=2; k<kNumCuts; ++k) {
		_nthMask[k] = _theMask;
		_nthMask[k].set(k,false);
//		std::cout << _nthMask[k].to_string() << std::endl;
	}

//	std::cout << "----" << std::endl;
//
//	std::cout << kCharge << "  " << _nthMask[kCharge].to_string() << std::endl;
//	std::cout << kZveto << "  " << _nthMask[kZveto].to_string() << std::endl;
//	std::cout << kMaxMll << "  " << _nthMask[kMaxMll].to_string() << std::endl;
//
//	std::cout << "----" << std::endl;
//
//	higgsBitWord wTest, wK;
//
//	wTest.set(kCharge,1).set(kD0,1).set(kDz,1)
//			.set(kMinMet,1).set(kMinMll,1).set(kZveto,1)
//			.set(kProjMet,1).set(kJetVeto,1).set(kSoftMuon,1)
//			.set(kHardPtMin,1).set(kSoftPtMin,1).set(kMaxMll,1).set(kDeltaPhi,1);
//
//	std::cout << _theMask.to_string() << "   " << wTest.to_string() << std::endl;
//	std::cout << "are the same?" << (_theMask == wTest) << std::endl;
//
//	std::cout << wK <<  "  " << (_theMask & wK).to_string() << std::endl;

//	THROW_RUNTIME("End Test");
}

//_____________________________________________________________________________
HWWAnalyzer::~HWWAnalyzer() {
	// TODO Auto-generated destructor stub
}

//_____________________________________________________________________________
void HWWAnalyzer::Book() {
	if (!_output) return;

	_output->cd();

	std::map<int,std::string> labels;

	labels[kDileptons] = "N_{dileptons}";
	labels[kCharge]    = "Opposite charge";
	labels[kD0]        = "D0";
	labels[kDz]        = "Dz";
	labels[kMinMet]    = "Met_{min}";
	labels[kMinMll]    = "m^{ll}_{min}";
	labels[kZveto]     = "Z veto";
	labels[kProjMet]   = "ProjMet";
	labels[kJetVeto]   = "n_{jets} == 0";
	labels[kSoftMuon]  = "No Soft #mu";
	labels[kMaxMll]    = "m^{ll}_{max}";
	labels[kHardPtMin] = "p^{hard}_{min}";
	labels[kSoftPtMin] = "p^{soft}_{min}";
	labels[kDeltaPhi]  = "#Delta#Phi_{ll}";


	_eeCounters = new TH1F("eeCounters","eeCounters",labels.size(),1,labels.size()+1);
	_mmCounters = new TH1F("mmCounters","mmCounters",labels.size(),1,labels.size()+1);
	_emCounters = new TH1F("emCounters","emCounters",labels.size(),1,labels.size()+1);
	_llCounters = new TH1F("llCounters","llCounters",labels.size(),1,labels.size()+1);

	std::map<int,std::string>::iterator it;
	for ( it = labels.begin(); it != labels.end(); ++it) {
		_eeCounters->GetXaxis()->SetBinLabel(it->first, it->second.c_str());
		_mmCounters->GetXaxis()->SetBinLabel(it->first, it->second.c_str());
		_emCounters->GetXaxis()->SetBinLabel(it->first, it->second.c_str());
		_llCounters->GetXaxis()->SetBinLabel(it->first, it->second.c_str());
	}

	_output->mkdir("ll")->cd();

	bookNm1Histograms( _llNm1Hist, "ll", "N-1 Plot - " );

	_output->mkdir("ee")->cd();
	bookNm1Histograms( _eeNm1Hist, "ll", "N-1 Plot - " );

	_output->mkdir("em")->cd();
	bookNm1Histograms( _emNm1Hist, "ll", "N-1 Plot - " );

	_output->mkdir("mm")->cd();
	bookNm1Histograms( _emNm1Hist, "ll", "N-1 Plot - " );

	_output->mkdir("test")->cd();
	bookNm1Histograms( _preCutHist, "pre", "PreCut - ");
	bookNm1Histograms( _postCutHist, "post", "PostCut - ");
	_output->cd();

	_analysisTree = new TTree(_analysisTreeName.c_str(),"HWW variables Tree");
	_analysisTree->Branch("nt","HWWNtuple",&_ntuple);

}

//_____________________________________________________________________________
void HWWAnalyzer::BeginJob() {
	_chain->SetBranchAddress("ev", &_event);

}

//_____________________________________________________________________________
void HWWAnalyzer::bookNm1Histograms( std::vector<TH1F*>& histograms , const std::string& nPrefix, const std::string& lPrefix ) {

	// all numbers to 0, just to be sure;
	histograms.assign(kNumCuts,0x0);

	histograms[kCharge] 	= new TH1F((nPrefix+"Charge").c_str(),   (lPrefix+"Charge").c_str(),3,-1,2);
	histograms[kD0]			= new TH1F((nPrefix+"D0").c_str(),       (lPrefix+"D0").c_str(), 100, -3*_maxD0, 3*_maxD0);
	histograms[kDz]			= new TH1F((nPrefix+"Dz").c_str(),       (lPrefix+"Dz").c_str(), 100, -3*_maxDz, 3*_maxDz);
	histograms[kMinMet]		= new TH1F((nPrefix+"MinMet").c_str(),   (lPrefix+"Met_{min}").c_str(), 100, 0, 100);
	histograms[kMinMll]		= new TH1F((nPrefix+"MinMll").c_str(),   (lPrefix+"m^{ll}_{min}").c_str(), 100, 0, 100);
	histograms[kZveto]		= new TH1F((nPrefix+"Zveto").c_str(),    (lPrefix+"Z veto").c_str(), 100, 0, 180);
	histograms[kProjMet]	= new TH1F((nPrefix+"ProjMet").c_str(),  (lPrefix+"Projected MET").c_str(), 100, 0, 50);
	histograms[kJetVeto]	= new TH1F((nPrefix+"JetVeto").c_str(),  (lPrefix+"n_{jets} = 0").c_str(), 20, 0, 20);
	histograms[0]	= new TH1F((nPrefix+"JetVetoAft").c_str(),  (lPrefix+"n_{jets} = 0 after").c_str(), 20, 0, 20);

	//	_llNm1Hist[kProjMet]	= new TH1F("llNm1ProjMet",  "N-1 plot = ProjMet");
//	_llNm1Hist[kJetVeto]	= new TH1F("llNm1JetVeto",  "N-1 plot = n_{jets} == 0");
//	_llNm1Hist[kSoftMuon]	= new TH1F("llNm1SoftMuon", "N-1 plot = No Soft #mu");
//	_llNm1Hist[kHardPtMin]	= new TH1F("llNm1HardPtMin","N-1 plot = m^{ll}_{max}");
//	_llNm1Hist[kSoftPtMin]	= new TH1F("llNm1SoftPtMin","N-1 plot = p^{hard}_{min}");
//	_llNm1Hist[kMaxMll]		= new TH1F("llNm1MaxMll",   "N-1 plot = p^{soft}_{min}");
//	_llNm1Hist[kDeltaPhi]	= new TH1F("llNm1DeltaPhi", "N-1 plot = #Delta#Phi_{ll}");

}

//_____________________________________________________________________________
void HWWAnalyzer::readHiggsCutSet( const std::string& path ) {

	std::cout << "Reading cuts from file " << path << std::endl;

	ifstream cutFile(path.c_str(), ifstream::in);
	if ( !cutFile.is_open() ) {
		THROW_RUNTIME(std::string("File ") + path + " not found");
	}

	std::string line;
	while( cutFile.good() ) {
		getline(cutFile, line);
		// remove trailing and leading spaces

		std::stringstream ss(line), ssTmp(line);
		std::string dummy, a;

		ssTmp >> dummy;
		if ( dummy.empty() || dummy[0]=='#') continue;

		HiggsCutSet h;
		ss >> h.hMass;

		ss >> h.minPtHard >> h.minPtSoft >> h.maxMll >> h.maxDphi;

		h.print();

		_cutVector.push_back(h);
	}
}

//_____________________________________________________________________________
HWWAnalyzer::HiggsCutSet HWWAnalyzer::getHiggsCutSet(int mass) {
	std::vector<HiggsCutSet>::iterator it;
	for ( it=_cutVector.begin(); it != _cutVector.end(); ++it) {
		if ( (*it).hMass == mass )
			return *it;
	}

	std::stringstream msg;
	msg << "Higgs Cut set " << mass << " not found";
	THROW_RUNTIME(msg.str());

}

//_____________________________________________________________________________
void HWWAnalyzer::calcNtuple(){

	TLorentzVector pA, pB;
	Int_t cA, cB;
	double d0A, d0B;
	double dZA, dZB;
	double maxProjMet;
	TH1F* counters;

    switch ( _event->NEles ) {
    case 2:
    	// A has the highst pT?
    	pA = _event->Els[0].ElP;
    	pB = _event->Els[1].ElP;

    	cA = _event->Els[0].ElCharge;
    	cB = _event->Els[1].ElCharge;

    	d0A = _event->Els[0].ElD0PV;
    	d0B = _event->Els[1].ElD0PV;

    	dZA = _event->Els[0].ElDzPV;
    	dZB = _event->Els[1].ElDzPV;

    	maxProjMet = _minProjMetLL;
    	counters = _eeCounters;
    	break;
    case 1:
    	if ( _event->Els[0].ElP.Pt() > _event->Mus[0].MuP.Pt() ) {
        	pA = _event->Els[0].ElP;
        	pB = _event->Mus[0].MuP;

        	cA = _event->Els[0].ElCharge;
        	cB = _event->Mus[0].MuCharge;

        	d0A = _event->Els[0].ElD0PV;
        	d0B = _event->Mus[0].MuD0PV;

        	dZA = _event->Els[0].ElDzPV;
        	dZB = _event->Mus[0].MuDzPV;
    	} else {
        	pA = _event->Mus[0].MuP;
        	pB = _event->Els[0].ElP;

        	cA = _event->Mus[0].MuCharge;
        	cB = _event->Els[0].ElCharge;

        	d0A = _event->Mus[0].MuD0PV;
        	d0B = _event->Els[0].ElD0PV;

        	dZA = _event->Mus[0].MuDzPV;
        	dZB = _event->Els[0].ElDzPV;
    	}

    	maxProjMet = _minProjMetEM;
    	counters = _emCounters;
    	break;
    case 0:
    	// A has the highst pT?
    	pA = _event->Mus[0].MuP;
    	pB = _event->Mus[1].MuP;

    	cA = _event->Mus[0].MuCharge;
    	cB = _event->Mus[1].MuCharge;

    	d0A = _event->Mus[0].MuD0PV;
    	d0B = _event->Mus[1].MuD0PV;

    	dZA = _event->Mus[0].MuDzPV;
    	dZB = _event->Mus[1].MuDzPV;

    	maxProjMet = _minProjMetLL;
    	counters = _mmCounters;
    	break;
    }

    // we work on the assumption A is the highet pT lepton, B is not. This is a watchdog
    if ( pB.Pt() > pA.Pt() ) {
    	THROW_RUNTIME("A.Pt < B.Pt");
    }

    // opposite charge
    bool oppositeCharge = ( cA*cB < 0 );

    // 3 - invariant mass
    double mll = (pA+pB).Mag();

    // 4a pfMet
	double pfMet = _event->PFMET;
	// 4b - muMet
	double muMet = _event->MuCorrMET;

	// 5 - projected MeT
	// 5a - projPfMet
	short i;

	TLorentzVector pfMetV;
	pfMetV.SetPtEtaPhiE(_event->PFMET, 0, _event->PFMETphi,0);

	double pfMetDphi = TMath::Min(TMath::Abs(pA.DeltaPhi(pfMetV)), TMath::Abs(pB.DeltaPhi(pfMetV)));
	double projPfMet = pfMetDphi < TMath::PiOver2() ? pfMet*TMath::Sin(pfMetDphi) : pfMet;


	// 5b - projMuMet
	TLorentzVector muMetV;
	muMetV.SetPtEtaPhiE(_event->MuCorrMET, 0, _event->MuCorrMETphi, 0);

	double muMetDphi = TMath::Min(TMath::Abs(pA.DeltaPhi(muMet)), TMath::Abs(pB.DeltaPhi(muMet)));
	double projMuMet = muMetDphi < TMath::PiOver2() ? muMet*TMath::Sin(muMetDphi) : muMet;

	// 6 - dPhiEE
	double dPhiLL = TMath::Abs(pA.DeltaPhi(pB));

	// 7 - jet veto
	// 7a - pf jets
	int nPfJets = _event->PFNJets;
	// 7b - calo jets
	int nJets   = _event->NJets;

	double pTHard = pA.Pt();
	double pTSoft = pB.Pt();

	// 8 soft  muon
	bool softMu = _event->HasSoftMus;

	_ntuple->type = _event->NEles;

    _ntuple->cA = cA;
    _ntuple->cB = cB;

    _ntuple->pA = pA;
    _ntuple->pB = pB;

    _ntuple->d0A = d0A;
    _ntuple->d0B = d0B;

    _ntuple->dZA = dZA;
    _ntuple->dZB = dZB;

	_ntuple->mll        = mll;
	_ntuple->pfMet      = pfMet;
	_ntuple->muMet      = muMet;
	_ntuple->projPfMet  = projPfMet;
	_ntuple->projMuMet  = projMuMet;
	_ntuple->dPhi     = dPhiLL;
	_ntuple->nPfJets	 = nPfJets;
	_ntuple->nJets      = nJets;
	_ntuple->softMu     = softMu;

	_analysisTree->Fill();

}

//_____________________________________________________________________________
void HWWAnalyzer::cutAndFill() {

	higgsBitWord word;


	word.set(kCharge, _ntuple->cA*_ntuple->cB < 0 );

	word.set(kD0, TMath::Abs(_ntuple->d0A) < _maxD0 && TMath::Abs(_ntuple->d0B) < _maxD0);

	word.set(kDz, TMath::Abs(_ntuple->dZA) < _maxDz && TMath::Abs(_ntuple->dZB) < _maxDz);

	word.set(kMinMet, _ntuple->pfMet > _minMet );

	word.set(kMinMll, _ntuple->type == 1 || _ntuple->mll > _minMll);

	word.set(kZveto, TMath::Abs(_ntuple->mll - _Z0->Mass()) > _zVetoWidth );

	float minProjMet = _ntuple->type == 1 ? _minProjMetEM : _minProjMetLL;
	word.set(kProjMet, _ntuple->projPfMet > minProjMet);

	word.set(kJetVeto, _ntuple->nPfJets == 0);

	word.set(kSoftMuon, _ntuple->softMu == 0);

	word.set(kHardPtMin, _ntuple->pA.Pt() > _theCuts.minPtHard);

	word.set(kSoftPtMin, _ntuple->pB.Pt() > _theCuts.minPtSoft);

	word.set(kMaxMll, _ntuple->type == 1 && _ntuple->mll < _theCuts.maxMll);

	word.set(kDeltaPhi, _ntuple->dPhi < _theCuts.maxDphi);


	// N-1 plots
	if ( (word & _nthMask[kCharge]) == _nthMask[kCharge] )
		_llNm1Hist[kCharge]->Fill(_ntuple->cA*_ntuple->cB);

	if ( (word & _nthMask[kD0]) == _nthMask[kD0]) {
		_llNm1Hist[kD0]->Fill(_ntuple->d0A);
		_llNm1Hist[kD0]->Fill(_ntuple->d0B);
	}

	if ( (word & _nthMask[kDz]) == _nthMask[kDz]) {
		_llNm1Hist[kDz]->Fill(_ntuple->dZA);
		_llNm1Hist[kDz]->Fill(_ntuple->dZB);
	}


	TH1F* counters(0x0);
	switch ( _ntuple->type ) {
	case 2:
		counters = _eeCounters;
		break;
	case 1:
		counters = _emCounters;
		break;
	case 0:
		counters = _mmCounters;
		break;
	default:
		THROW_RUNTIME("Wrong event type (NEles): " << _ntuple->type );
	};

	counters->Fill(kDileptons);
	// opposite charge
	_preCutHist[kCharge]->Fill(_ntuple->cA*_ntuple->cB);
	if ( !word[kCharge] ) return;
	counters->Fill(kCharge);
	_postCutHist[kCharge]->Fill(_ntuple->cA*_ntuple->cB);

	// d0
	_preCutHist[kD0]->Fill( _ntuple->d0A );
	_preCutHist[kD0]->Fill( _ntuple->d0B );
	if ( !word[kD0]) return;
	counters->Fill(kD0);
	_postCutHist[kD0]->Fill( _ntuple->d0A );
	_postCutHist[kD0]->Fill( _ntuple->d0B );

	// dz
	_preCutHist[kDz]->Fill( _ntuple->dZA );
	_preCutHist[kDz]->Fill( _ntuple->dZB );
	if ( !word[kDz] ) return;
	counters->Fill(kDz);
	_postCutHist[kDz]->Fill( _ntuple->dZA );
	_postCutHist[kDz]->Fill( _ntuple->dZB );


	// min missing Et
	_preCutHist[kMinMet]->Fill(_ntuple->pfMet);
	if ( !word[kMinMet] ) return;
	counters->Fill(kMinMet);
	_postCutHist[kMinMet]->Fill(_ntuple->pfMet);

	// min invariant mass
	_preCutHist[kMinMll]->Fill(_ntuple->mll);
	if ( !word[kMinMll] ) return;
	counters->Fill(kMinMll);
	_postCutHist[kMinMll]->Fill(_ntuple->mll);

	// Z veto (m_ll-m_Z < 15 GeV)
	_preCutHist[kZveto]->Fill(_ntuple->mll);
	if ( !word[kZveto] ) return;
	counters->Fill(kZveto);
	_postCutHist[kZveto]->Fill(_ntuple->mll);

	// proj Met (20 GeV for ee)
	_preCutHist[kProjMet]->Fill(_ntuple->projPfMet);
	if ( !word[kProjMet] ) return;
	counters->Fill(kProjMet);
	_postCutHist[kProjMet]->Fill(_ntuple->projPfMet);

	// njets == 0
	_preCutHist[kJetVeto]->Fill(_ntuple->nPfJets);
	if ( !word[kJetVeto] ) return;
	counters->Fill(kJetVeto);
	_postCutHist[kJetVeto]->Fill(_ntuple->nPfJets);

	// soft muon
	if ( !word[kSoftMuon] ) return;
	counters->Fill(kSoftMuon);

	// hard pt cut
	if ( !word[kHardPtMin] ) return;
	counters->Fill(kHardPtMin);

	// soft pt cut
	if ( !word[kSoftPtMin] ) return;
	counters->Fill(kSoftPtMin);

	// Mll_max
	if ( !word[kMaxMll] ) return;
	counters->Fill(kMaxMll);

	// delta phi
	if ( !word[kDeltaPhi] ) return;
	counters->Fill(kDeltaPhi);

}

//_____________________________________________________________________________
void HWWAnalyzer::Process( Long64_t iEvent ) {
//	std::cout << iEvent <<  std::endl;
	_chain->GetEntry(iEvent);

	_ntuple->Clear();

	if ( _event->NEles + _event->NMus != 2 )
		THROW_RUNTIME("Wrong number of leptons in the event: NEles = " << _event->NEles << " NMus = " << _event->NMus  );

	calcNtuple();
	cutAndFill();

}

//_____________________________________________________________________________
void HWWAnalyzer::EndJob() {

	for ( int i(1); i<= _llCounters->GetNbinsX(); ++i) {
		float binc(0);
		binc += _eeCounters->GetBinContent(i);
		binc += _mmCounters->GetBinContent(i);
		binc += _emCounters->GetBinContent(i);

		_llCounters->SetBinContent(i,binc);
	}
}
