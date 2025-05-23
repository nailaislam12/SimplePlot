def set_branches(final_state_mode, era, DeepTau_version, process="None", temp_version="None"):
  common_branches = [
    "run", "luminosityBlock", "event", "Generator_weight", "NWEvents", "XSecMCweight",
    "TauSFweight", "MuSFweight", "ElSFweight", "BTagSFfull", 
    "Weight_DY_Zpt", "PUweight", "Weight_TTbar_NNLO",
    "FFweight", "FFweight_QCD", "FFweight_WJ", "FFweight_FractionQCD",
    "FSLeptons", "Lepton_pt", "Lepton_eta", "Lepton_phi", "Lepton_iso",
    "Tau_genPartFlav", "Tau_decayMode",
    #"nTightCleanJet", "TightCleanJet_pt", "TightCleanJet_cjetIdx",
    "nCleanJet", "CleanJet_pt", "CleanJet_eta", "CleanJet_phi", "CleanJet_mass",
    "HTT_m_vis", "HTT_dR", "HTT_pT_l1l2", 
    "FastMTT_mT", "FastMTT_mass",
    "HTT_pdgId",
    "Tau_rawPNetVSjet", "Tau_rawPNetVSmu", "Tau_rawPNetVSe",
    "PV_npvs", "Pileup_nPU",
    "HTT_H_pt", "HTT_mT_l1l2met",
    #"HTT_DiJet_dEta_fromHighestMjj", "HTT_DiJet_MassInv_fromHighestMjj",
    "HTT_DiJet_dEta_fromLeadingJets", "HTT_DiJet_MassInv_fromLeadingJets",
    #"HTT_DiJet_j1index", "HTT_DiJet_j2index",
    #"StitchWeight_WJets_NLO",
  ]
  branches = common_branches
  branches = add_final_state_branches(branches, final_state_mode)
  if final_state_mode != ["emu","dimuon"]: branches = add_DeepTau_branches(branches, DeepTau_version)
  branches = add_trigger_branches(branches, era, final_state_mode)
  if ("_TauTau" in process): branches = add_signal_branches(branches)

  return branches


def add_final_state_branches(branches_, final_state_mode):
  """ Helper function to add only relevant branches to loaded branches based on final state """
  final_state_branches = {
    "ditau"  : ["Lepton_tauIdx", "Lepton_mass", "Tau_dxy", "Tau_dz", "Tau_charge", "PuppiMET_pt", "PuppiMET_phi",
                "Tau_flightLengthSig", "Tau_flightLengthX", "Tau_flightLengthY", "Tau_flightLengthZ", 
                "Tau_ipLengthSig", "Tau_ip3d", "Tau_track_lambda", "Tau_track_qoverp",
               ],

    "mutau"  : ["Muon_dxy", "Muon_dz", "Muon_charge", "Muon_mass", "Muon_tightId", 
                "Lepton_mass", "Tau_dxy", "Tau_dz", "Tau_charge", "Tau_leadTkPtOverTauPt",
                "Lepton_tauIdx", "Lepton_muIdx",
                "PuppiMET_pt", "PuppiMET_phi", "CleanJet_btagWP", "HTT_mT_lmet"],

    "etau"   : ["Electron_dxy", "Electron_dz", "Electron_charge", "Electron_mass",
                "Lepton_mass", "Tau_dxy", "Tau_dz", "Tau_charge", 
                "Lepton_tauIdx", "Lepton_elIdx",
                "PuppiMET_pt", "PuppiMET_phi", "CleanJet_btagWP", "HTT_mT_lmet"],

    "dimuon" : ["Lepton_pdgId", "Lepton_muIdx",
                "Muon_dxy", "Muon_dz", "Muon_charge",
                "PuppiMET_pt", "PuppiMET_phi", "CleanJet_btagWP"],

    "emu"   : ["Electron_dxy", "Electron_dz", "Electron_charge", 
                "Muon_dxy", "Muon_dz", "Muon_charge", 
                "Lepton_elIdx", "Lepton_muIdx",
                "PuppiMET_pt", "PuppiMET_phi", "Lepton_tauIdx", 
                "Electron_mass", "Muon_mass",
                "CleanJet_btagWP", "HTT_DZeta", "HTT_mT_l1l2met"],
  }

  branch_to_add = final_state_branches[final_state_mode]
  for new_branch in branch_to_add:
    branches_.append(new_branch)
  
  return branches_


from triggers_dictionary import triggers_dictionary

def add_trigger_branches(branches_, era, final_state_mode):
  '''
  Helper function to add HLT branches used by a given final state
  '''
  era_year = "2022" if "2022" in era else "2023"
  for trigger in triggers_dictionary[era_year][final_state_mode]:
    branches_.append(trigger)

  return branches_


def add_DeepTau_branches(branches_, DeepTauVersion):
  ''' Helper function to add DeepTauID branches '''
  if DeepTauVersion == "2p1":
    for DeepTau_v2p1_branch in ["Tau_idDeepTau2017v2p1VSjet", "Tau_idDeepTau2017v2p1VSmu", "Tau_idDeepTau2017v2p1VSe"]:
      branches_.append(DeepTau_v2p1_branch)

  elif DeepTauVersion == "2p5":
    for DeepTau_v2p5_branch in ["Tau_idDeepTau2018v2p5VSjet", "Tau_idDeepTau2018v2p5VSmu", "Tau_idDeepTau2018v2p5VSe"]:
      branches_.append(DeepTau_v2p5_branch)

  else:
    print(f"no branches added with argument {DeepTauVersion}. Try 2p1 or 2p5.")

  return branches_


def add_signal_branches(branches_):
  gen_signal_branches = [
    "Gen_HTT_FS",
    "Gen_pT_l1", "Gen_eta_l1", "Gen_phi_l1",
    "Gen_pT_l2", "Gen_eta_l2", "Gen_phi_l2",
    "Gen_H_pT", "Gen_H_pT_fidMET",
    "Gen_pT_ll", "Gen_m_ll",
    "Gen_mT", "Gen_mT_fidMET",
    "Gen_DZeta", "Gen_DZeta_fidMET", 
    "Gen_deltaR_ll", "Gen_deltaEta_ll", "Gen_deltaPhi_ll",
    "Gen_nCleanJet",
    "Gen_pT_j1", "Gen_eta_j1", "Gen_phi_j1",
    "Gen_pT_j2", "Gen_eta_j2", "Gen_phi_j2",
    "Gen_pT_j3", "Gen_eta_j3", "Gen_phi_j3",
    "Gen_mjj", "Gen_deltaEta_jj",
  ]
  for branch in gen_signal_branches:
    branches_.append(branch)

  return branches_
