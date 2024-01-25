import numpy as np

### README ###
# binning for different variables are defined below and are separated by use-case
# All variables are assumed to be linearly binned.
 
binning_dictionary = {
#  var  : (nBins, xmin, xmax),

#  ditau
  "FS_t1_pt"   : (36, 0, 180),
  "FS_t1_eta"  : (30, -3, 3),
  "FS_t1_phi"  : (32, -3.2, 3.2),
  "FS_t1_DT"   : (9, 0, 9),
  "FS_t1_dxy"  : (50, 0, 0.20),
  "FS_t1_dz"   : (50, 0, 0.25),
  "FS_t1_chg"  : (2, -1, 1),

  "FS_t2_pt"   : (24, 0, 120),
  "FS_t2_eta"  : (30, -3, 3),
  "FS_t2_phi"  : (32, -3.2, 3.2),
  "FS_t2_DT"   : (9, 0, 9),
  "FS_t2_dxy"  : (50, 0, 0.20),
  "FS_t2_dz"   : (50, 0, 0.25),
  "FS_t2_chg"  : (2, -1, 1),

#  mutau/etau
  "FS_mu_pt"   : (40, 0, 120),
  "FS_mu_eta"  : (30, -3, 3),
  "FS_mu_phi"  : (32, -3.2, 3.2),
  "FS_mu_iso"  : (25, 0, 1),
  "FS_mu_dxy"  : (50, 0, 0.05),
  "FS_mu_dz"   : (50, 0, 0.25),
  "FS_mu_chg"  : (2, -1, 1),

  "FS_el_pt"   : (40, 0, 120),
  "FS_el_eta"  : (30, -3, 3),
  "FS_el_phi"  : (32, -3.2, 3.2),
  "FS_el_iso"  : (25, 0, 1),
  "FS_el_dxy"  : (50, 0, 0.05),
  "FS_el_dz"   : (50, 0, 0.25),
  "FS_el_chg"  : (2, -1, 1),

  "FS_tau_pt"  : (36, 0, 180),
  "FS_tau_eta" : (30, -3, 3),
  "FS_tau_phi" : (32, -3.2, 3.2),
  "FS_tau_dxy" : (50, 0, 0.20),
  "FS_tau_dz"  : (50, 0, 0.25),
  "FS_tau_chg" : (2, -1, 1),

  "FS_tau_rawPNetVSjet" : (50, 0, 1),
  "FS_tau_rawPNetVSmu"  : np.array([0, 0.95, 0.96, 0.97, 0.98, 0.99, 1]), # plot logx
  "FS_tau_rawPNetVSe"   : np.array([0, 0.95, 0.96, 0.97, 0.98, 0.99, 1]),

  "FS_t1_rawPNetVSjet" : (50, 0, 1),
  "FS_t1_rawPNetVSmu"  : np.array([0, 0.95, 0.96, 0.97, 0.98, 0.99, 1]), # plot logx
  "FS_t1_rawPNetVSe"   : np.array([0, 0.95, 0.96, 0.97, 0.98, 0.99, 1]),

  "FS_t2_rawPNetVSjet" : (50, 0, 1),
  "FS_t2_rawPNetVSmu"  : np.array([0, 0.95, 0.96, 0.97, 0.98, 0.99, 1]), # plot logx
  "FS_t2_rawPNetVSe"   : np.array([0, 0.95, 0.96, 0.97, 0.98, 0.99, 1]),

  "mutau_TnP" : {
    "FS_mu_pt"   : (40, 0, 120),
    "FS_mu_eta"  : (7, -2.7, 2.7),
    "FS_mu_phi"  : (16, -3.2, 3.2),
 
    "FS_tau_pt" : np.array([0, 20, 25, 30, 35, 40, 50, 70, 150]),
    "FS_tau_eta"  : (7, -2.7, 2.7),
    "FS_tau_phi" : (16, -3.2, 3.2),
  },
  "pass_tag"   : (2, 0, 2),
  "pass_probe" : (2, 0, 2),

# dimuon
  "FS_m1_pt"   : (60, 0, 300),
  "FS_m1_eta"  : (99, -2.5, 2.5),
  "FS_m1_phi"  : (64, -3.2, 3.2),
  "FS_m1_iso"  : (25, 0, 1),
  "FS_m1_dxy"  : (50, 0, 0.05),
  "FS_m1_dz"   : (50, 0, 0.25),
  "FS_m1_chg"  : (2, -1, 1),

  "FS_m2_pt"   : (60, 0, 300),
  "FS_m2_eta"  : (99, -2.5, 2.5),
  "FS_m2_phi"  : (64, -3.2, 3.2),
  "FS_m2_iso"  : (25, 0, 1),
  "FS_m2_dxy"  : (50, 0, 0.05),
  "FS_m2_dz"   : (50, 0, 0.25),
  "FS_m2_chg"  : (2, -1, 1),
  "FS_m_vis_tight" : (80, 70, 110), # TODO add this

# common, calculated on the fly
  "FS_mt"         : (40, 0, 200),
  "nCleanJetGT30" : (8, 0, 8), # GT(E) = Greater Than (Equal to)
  "CleanJetGT30_pt_1"  : (60, 0, 300),
  "CleanJetGT30_pt_2"  : (60, 0, 300),
  "CleanJetGT30_pt_3"  : (60, 0, 300),
  "CleanJetGT30_eta_1" : (50, -5, 5),
  "CleanJetGT30_eta_2" : (50, -5, 5),
  "CleanJetGT30_eta_3" : (50, -5, 5),
  "CleanJetGT30_phi_1" : (16, -3.2, 3.2),
  "CleanJetGT30_phi_2" : (16, -3.2, 3.2),
  "CleanJetGT30_phi_3" : (16, -3.2, 3.2),
  "FS_mjj"    : (30, 0, 1500),
  "FS_detajj" : (31, 0, 7),

# common, from branches
  "MET_pt"      : (30, 0, 150),
  "PuppiMET_pt" : (50, 0, 150),
  "nCleanJet"   : (8, 0, 8),
  "CleanJet_pt" : (30, 20, 200),
  "CleanJet_eta": (50, -5, 5),
  "HTT_DiJet_MassInv_fromHighestMjj" : (30, 0, 1500),
  "HTT_DiJet_dEta_fromHighestMjj"    : (35, 0, 7),
  "HTT_H_pt_using_PUPPI_MET"         : (30, 0, 300),
  "HTT_dR"     : (60, 0, 6),
  "HTT_m_vis-KSUbinning" : (30, 0, 300),
  "HTT_m_vis-SFbinning"  : (40, 0, 200),
  "HTT_pT_l1l2" : (30, 0, 150),
  "FastMTT_PUPPIMET_mT" : (40, 0, 400),
  "FastMTT_PUPPIMET_mass" : (20, 0, 400),
  "FS_t1_flav" : (11, 0, 11),
  "FS_t2_flav" : (11, 0, 11),
  "PV_npvs"    : (30, 0, 90),
}
