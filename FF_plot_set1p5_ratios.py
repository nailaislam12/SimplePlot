# Authored by Braden Allmond, Sep 11, 2023

# libraries
import numpy as np
import sys
import matplotlib.pyplot as plt
import gc
import copy
from iminuit import Minuit
from iminuit.cost import LeastSquares

# explicitly import used functions from user files, grouped roughly by call order and relatedness
from file_map_dictionary   import testing_file_map, full_file_map, testing_dimuon_file_map, dimuon_file_map
from file_map_dictionary   import pre2022_file_map
from file_functions        import load_process_from_file, append_to_combined_processes, sort_combined_processes

from luminosity_dictionary import luminosities_with_normtag as luminosities

from cut_and_study_functions import set_branches, set_vars_to_plot, set_good_events
from cut_and_study_functions import apply_HTT_FS_cuts_to_process, apply_AR_cut

from plotting_functions    import get_binned_data, get_binned_backgrounds, get_binned_signals
from plotting_functions    import setup_ratio_plot, make_ratio_plot, spruce_up_plot, spruce_up_legend
from plotting_functions    import plot_data, plot_MC, plot_signal, make_bins

from plotting_functions import get_midpoints, setup_single_plot, spruce_up_single_plot

from calculate_functions   import calculate_signal_background_ratio, yields_for_CSV
from utility_functions     import time_print, make_directory, print_setup_info, log_print

from cut_and_study_functions import append_lepton_indices, apply_cut, apply_jet_cut, add_FF_weights
from cut_and_study_functions import load_and_store_NWEvents, customize_DY, append_flavor_indices, set_protected_branches

from cut_ditau_functions import make_ditau_cut
from cut_mutau_functions import make_mutau_cut
from FF_functions import *

from binning_dictionary import label_dictionary

#def line(x, a, b):
#    return a + x * b

def line_np(x, par):
    return np.polyval(par, x)  # for len(par) == 2, this is a line

def make_fit(method, order):
  nvals = order + 1
  starting_vals = [5]*nvals
  name_string = "abcdefghijklmnop" # order > 10
  name_vals = [name_string[i] for i in range(nvals)]
  m = Minuit(least_squares, starting_vals, name=name_vals)
  m.migrad()
  #print(m)

  # check reduced chi2, goodness-of-fit estimate, should be around 1 # from Minuit manual
  chi_squared = m.fval 
  ndof =  len(use_FF_ratio) - len(m.values)
  reduced_chi_squared = chi_squared / ndof

  y_eqn = make_order_label(order, m.values)
  label = f"{y_eqn}\
          \n$\chi^2$/ndof = {chi_squared:.2f}/{ndof} = {reduced_chi_squared:.2f}"

  return m.values, label # m.values returns highest order first

def make_order_label(order, fit_values):
  nfit_values = len(fit_values)
  label = "y ="
  for i,val in enumerate(fit_values):
    label += f" + {val:.2e}*x^{nfit_values - i - 1}"
  label = label.replace("*x^0", "")
  return label


if __name__ == "__main__":
  '''
  '''

  import argparse 
  parser = argparse.ArgumentParser(description='Make a standard Data-MC agreement plot.')
  # store_true : when the argument is supplied, store it's value as true
  # for 'testing' below, the default value is false if the argument is not specified
  parser.add_argument('--testing',     dest='testing',     default=False,       action='store_true')
  parser.add_argument('--hide_plots',  dest='hide_plots',  default=False,       action='store_true')
  parser.add_argument('--hide_yields', dest='hide_yields', default=False,       action='store_true')
  parser.add_argument('--final_state', dest='final_state', default="mutau",     action='store')
  parser.add_argument('--plot_dir',    dest='plot_dir',    default="plots",     action='store')
  parser.add_argument('--lumi',        dest='lumi',        default="2022 EFG",  action='store')
  parser.add_argument('--jet_mode',    dest='jet_mode',    default="Inclusive", action='store')
  parser.add_argument('--DeepTau',     dest='DeepTau_version', default="2p5",   action='store')
  parser.add_argument('--use_DY_NLO',  dest='use_DY_NLO',  default=True,        action='store')

  args = parser.parse_args() 
  testing     = args.testing     # False by default, do full dataset unless otherwise specified
  hide_plots  = args.hide_plots  # False by default, show plots unless otherwise specified
  hide_yields = args.hide_yields # False by default, show yields unless otherwise specified
  use_DY_NLO  = args.use_DY_NLO  # True  by default, use LO DY if False
  lumi = luminosities["2022 G"] if testing else luminosities[args.lumi]
  DeepTau_version = args.DeepTau_version # default is 2p5 [possible values 2p1 and 2p5]

  # final_state_mode affects many things automatically, including good_events, datasets, plotting vars, etc.
  final_state_mode = args.final_state # default mutau [possible values ditau, mutau, etau, dimuon]
  jet_mode         = args.jet_mode # default Inclusive [possible values 0j, 1j, 2j, GTE2j]

  #lxplus_redirector = "root://cms-xrd-global.cern.ch//"
  eos_user_dir    = "/eos/user/b/ballmond/NanoTauAnalysis/analysis/HTauTau_2022_fromstep1_skimmed/" + final_state_mode
  # there's no place like home :)
  home_dir        = "/Users/ballmond/LocalDesktop/HiggsTauTau/Run3PreEEFSSplitSamples/" + final_state_mode
  era_modifier_2022 = "preEE" if (("C" in args.lumi) or ("D" in args.lumi)) else "postEE"
  home_dir        = "/Users/ballmond/LocalDesktop/HiggsTauTau/V12_PFRel_"+era_modifier_2022+"_Run3FSSplitSamples/" + final_state_mode
  using_directory = home_dir
 
  good_events  = set_good_events(final_state_mode)
  branches     = set_branches(final_state_mode, DeepTau_version)
  vars_to_plot = set_vars_to_plot(final_state_mode, jet_mode=jet_mode)
  plot_dir_name = "FS_plots_testing/" if testing==True else "FS_plots/"
  plot_dir = make_directory(plot_dir_name+args.plot_dir, final_state_mode+"_"+jet_mode, testing=testing)

  log_file = open('outputfile.log', 'w')
  # show info to user
  print_setup_info(final_state_mode, lumi, jet_mode, testing, DeepTau_version,
                   using_directory, plot_dir,
                   good_events, branches, vars_to_plot, log_file)

  file_map = testing_file_map if testing else full_file_map
  if (use_DY_NLO == True): 
    file_map.pop("DYInc")
    file_map.pop("WJetsInc")
  else: 
    file_map.pop("DYIncNLO")
    file_map.pop("WJetsIncNLO")

  common_selection = "(METfilters) & (LeptonVeto==0) & (JetMapVeto_EE_30GeV) & (JetMapVeto_HotCold_30GeV)"
  ditau_selection  = common_selection + " & (abs(HTT_pdgId)==15*15) & (Trigger_ditau)"
  mutau_selection  = common_selection + " & (abs(HTT_pdgId)==13*15) & (Trigger_mutau)"
  final_state_selection_dict = {"ditau": ditau_selection, "mutau" : mutau_selection}
  base_selection = final_state_selection_dict[final_state_mode]

  dataset_dictionary = {"ditau" : "DataTau", "mutau" : "DataMuon", "etau" : "DataElectron", "emu" : "DataEMu"}
  reject_dataset_dictionary = {"ditau" : ["DataMuon", "DataElectron", "DataEMu"],
                               "mutau" : ["DataTau",  "DataElectron", "DataEMu"],
                               "etau"  : ["DataMuon", "DataTau",      "DataEMu"],
                               "emu"   : ["DataMuon", "DataElectron", "DataTau"]}

  dataset = dataset_dictionary[final_state_mode]
  reject_datasets = reject_dataset_dictionary[final_state_mode]

  store_region_data_dictionary = {}
  store_region_bkgd_dictionary = {}
  store_region_sgnl_dictionary = {}
  semilep_mode = "QCD" # "QCD" or "WJ"
  numerator = "DRsr_aiso"
  denominator = "DRar_aiso"
  for region in [numerator, denominator]:

    vars_to_plot = set_vars_to_plot(final_state_mode, jet_mode=jet_mode)

    # make and apply cuts to any loaded events, store in new dictionaries for plotting
    combined_process_dictionary = {}

    for process in file_map: 

      gc.collect()
      if (process in reject_datasets): continue

      new_process_dictionary = load_process_from_file(process, using_directory, file_map, log_file,
                                              branches, base_selection, final_state_mode,
                                              data=("Data" in process), testing=testing)
      event_dictionary = new_process_dictionary[process]["info"]
      if (event_dictionary == None): continue

      protected_branches = ["None"]
      event_dictionary = append_lepton_indices(event_dictionary)
      if ("Data" not in process):
        load_and_store_NWEvents(process, event_dictionary)
        if ("DY" in process): customize_DY(process, final_state_mode)
        event_dictionary = append_flavor_indices(event_dictionary, final_state_mode, keep_fakes=True)

      event_dictionary = FF_control_flow(final_state_mode, semilep_mode, region, event_dictionary, DeepTau_version)
      event_dictionary = apply_cut(event_dictionary, "pass_"+region+"_cuts", protected_branches)

      if (event_dictionary==None or len(event_dictionary["run"])==0): continue
      event_dictionary   = apply_jet_cut(event_dictionary, jet_mode)
      if (event_dictionary==None or len(event_dictionary["run"])==0): continue

      if (final_state_mode == "ditau"):
        event_dictionary   = make_ditau_cut(event_dictionary, DeepTau_version) # no DeepTau or Charge requirements
        if (event_dictionary==None or len(event_dictionary["run"])==0): continue

      if (final_state_mode == "mutau"):
        event_dictionary   = make_mutau_cut(event_dictionary, DeepTau_version) # no DeepTau or Charge requirements
        if (event_dictionary==None or len(event_dictionary["run"])==0): continue

      protected_branches = set_protected_branches(final_state_mode=final_state_mode, jet_mode="none")
      event_dictionary   = apply_cut(event_dictionary, "pass_cuts", protected_branches)
      if (event_dictionary==None or len(event_dictionary["run"])==0): continue


      # TODO : extendable to jet cuts (something I've meant to do for some time)
      if "DY" in process:
        event_flavor_arr = event_dictionary["event_flavor"]
        pass_gen_flav, pass_lep_flav, pass_jet_flav = [], [], []
        for i, event_flavor in enumerate(event_flavor_arr):
          if event_flavor == "G":
            pass_gen_flav.append(i)
          if event_flavor == "L":
            pass_lep_flav.append(i)
          if event_flavor == "J":
            pass_jet_flav.append(i)
      
        from cut_and_study_functions import apply_cut, set_protected_branches
        protected_branches = set_protected_branches(final_state_mode="none", jet_mode="Inclusive")
        background_gen_deepcopy = copy.deepcopy(event_dictionary)
        background_gen_deepcopy["pass_flavor_cut"] = np.array(pass_gen_flav)
        background_gen_deepcopy = apply_cut(background_gen_deepcopy, "pass_flavor_cut", protected_branches)
        if background_gen_deepcopy == None: continue

        background_lep_deepcopy = copy.deepcopy(event_dictionary)
        background_lep_deepcopy["pass_flavor_cut"] = np.array(pass_lep_flav)
        background_lep_deepcopy = apply_cut(background_lep_deepcopy, "pass_flavor_cut", protected_branches)
        if background_lep_deepcopy == None: continue

        background_jet_deepcopy = copy.deepcopy(event_dictionary)
        background_jet_deepcopy["pass_flavor_cut"] = np.array(pass_jet_flav)
        background_jet_deepcopy = apply_cut(background_jet_deepcopy, "pass_flavor_cut", protected_branches)
        if background_jet_deepcopy == None: continue

        combined_process_dictionary = append_to_combined_processes("DYGen", background_gen_deepcopy, vars_to_plot, 
                                                                   combined_process_dictionary)
        combined_process_dictionary = append_to_combined_processes("DYLep", background_lep_deepcopy, vars_to_plot, 
                                                                   combined_process_dictionary)
        combined_process_dictionary = append_to_combined_processes("DYJet", background_jet_deepcopy, vars_to_plot, 
                                                                   combined_process_dictionary)
        
      else:
        combined_process_dictionary = append_to_combined_processes(process, event_dictionary, vars_to_plot, 
                                                                   combined_process_dictionary)

    # after loop, sort big dictionary into three smaller ones
    data_dictionary, background_dictionary, signal_dictionary = sort_combined_processes(combined_process_dictionary)

    # store dictionaries
    store_region_data_dictionary[region] = data_dictionary
    store_region_bkgd_dictionary[region] = background_dictionary
    store_region_sgnl_dictionary[region] = signal_dictionary


  numerator_data = store_region_data_dictionary[numerator]
  numerator_bkgd = store_region_bkgd_dictionary[numerator]
  numerator_sgnl = store_region_sgnl_dictionary[numerator]
  denominator_data = store_region_data_dictionary[denominator]
  denominator_bkgd = store_region_bkgd_dictionary[denominator]
  denominator_sgnl = store_region_sgnl_dictionary[denominator]

  log_print("Processing finished!", log_file, time=True)
  ## end processing loop, begin plotting

  vars_to_plot = [var for var in vars_to_plot if "flav" not in var]
  # remove mvis, replace with mvis_HTT and mvis_SF
  vars_to_plot.remove("HTT_m_vis")
  vars_to_plot.append("HTT_m_vis-KSUbinning")
  if (final_state_mode == "ditau"):
    vars_to_plot = ["HTT_m_vis-KSUbinning", 
                  "FS_t1_pt", "FS_t1_eta", "FS_t1_phi",
                  "FS_t2_pt", "FS_t2_eta", "FS_t2_phi", "PuppiMET_pt"]
  if (final_state_mode == "mutau"):
    vars_to_plot = ["HTT_m_vis-KSUbinning", 
                  "FS_tau_pt", "FS_tau_eta", "FS_tau_phi",
                  "FS_mu_pt", "FS_mu_eta", "FS_mu_phi", "PuppiMET_pt", "FS_mt"]
  # and add back variables unique to the jet mode
  if (jet_mode == "1j") or (jet_mode == "GTE2j"): vars_to_plot.append("CleanJetGT30_pt_1")
  if (jet_mode == "GTE2j"): vars_to_plot.append("CleanJetGT30_pt_2")
  for var in vars_to_plot:
    log_print(f"Plotting {var}", log_file, time=True)

    xbins = make_bins(var, final_state_mode)

    ax_compare = setup_single_plot()
    ax_ratio   = setup_single_plot()

    temp_var = var
    if "HTT_m_vis" in var: var = "HTT_m_vis"
    h_numerator_data = get_binned_data(numerator_data, var, xbins, lumi)
    h_denominator_data = get_binned_data(denominator_data, var, xbins, lumi)
    h_numerator_backgrounds, h_numerator_summed_backgrounds = get_binned_backgrounds(numerator_bkgd, var, xbins, lumi, jet_mode)
    h_denominator_backgrounds, h_denominator_summed_backgrounds = get_binned_backgrounds(denominator_bkgd, var, xbins, lumi, jet_mode)
    var = temp_var

    h_numerator_data_m_MC = h_numerator_data - h_numerator_summed_backgrounds
    h_denominator_data_m_MC = h_denominator_data - h_denominator_summed_backgrounds

    # reversed dictionary search for era name based on lumi 
    title_era = [key for key in luminosities.items() if key[1] == lumi][0][0]
    title = f"{title_era}, {lumi:.2f}" + r"$fb^{-1}$"

    # plot everything :)
    plot_data(ax_compare, xbins, h_numerator_data_m_MC, lumi, color="black", label=f"{numerator} : Data-MC")
    plot_data(ax_compare, xbins, h_denominator_data_m_MC, lumi, color="green",  label=f"{denominator} : Data-MC")
    spruce_up_single_plot(ax_compare, label_dictionary[var], "Events/Bin", title, final_state_mode, jet_mode)
    plt.savefig(plot_dir + "/" + str(var) + "_" + str(region) + ".png")

    FF_ratio, FF_ratio_err = make_ratio_plot(ax_ratio, xbins, h_numerator_data_m_MC, h_denominator_data_m_MC, 
                                             label=f"{numerator} / {denominator}")

    # remove entry if val or error is zero (and is next to another zero)
    identify_zeros = np.array([(FF_ratio[i] == 0) for i in range(len(FF_ratio))]) # mask for all zeros
    # finds zeros neighboring zeros
    silly_zeros = []
    for i,val in enumerate(FF_ratio):
      if (val == 0):
        if (i == 0):
          if (FF_ratio[i+1] == 0): silly_zeros.append(True)
          else: silly_zeros.append(False)
        elif (i == len(FF_ratio)-1):
          if (FF_ratio[i-1] == 0): silly_zeros.append(True)
          else: silly_zeros.append(False)
        elif ((FF_ratio[i+1] == 0) or (FF_ratio[i-1] == 0)): silly_zeros.append(True)
        else: silly_zeros.append(False)
      else: silly_zeros.append(False)
    silly_zeros = np.array(silly_zeros)

    midpoints = get_midpoints(xbins)

    # cludging
    use_FF_ratio     = FF_ratio[~silly_zeros]
    use_FF_ratio_err = FF_ratio_err[~silly_zeros]
    use_midpoints    = midpoints[~silly_zeros]

    if (var == "FS_t1_pt") or (var == "FS_tau_pt"):
      use_vals = np.array([((midpoints[i] > 40) and (midpoints[i] < 150)) for i in range(len(midpoints))])
      use_FF_ratio     = FF_ratio[use_vals]
      use_FF_ratio_err = FF_ratio_err[use_vals]
      use_midpoints    = midpoints[use_vals]

    least_squares = LeastSquares(use_midpoints, use_FF_ratio, use_FF_ratio_err, line_np) # line is a function defined above

    # "Fo2" = Fit, order 2
    Fo0_values, Fo0_label = make_fit(least_squares, 0) # const
    Fo1_values, Fo1_label = make_fit(least_squares, 1) # line # want "order 1" to mean line
    Fo2_values, Fo2_label = make_fit(least_squares, 2) # qaudratic
    Fo3_values, Fo3_label = make_fit(least_squares, 3) # 3rd order polynomial
    Fo4_values, Fo4_label = make_fit(least_squares, 4) # 4th order polynomial

    # check reduced chi2, goodness-of-fit estimate, should be around 1 # from Minuit manual

    # need to store line and label of each fit
    ax_ratio.plot(use_midpoints, line_np(use_midpoints, (Fo0_values)), color="blue",   label="0th order")
    ax_ratio.plot(use_midpoints, line_np(use_midpoints, (Fo1_values)), color="red",    label="1st order")
    ax_ratio.plot(use_midpoints, line_np(use_midpoints, (Fo2_values)), color="green",  label="2nd order")
    ax_ratio.plot(use_midpoints, line_np(use_midpoints, (Fo3_values)), color="pink",   label="3rd order")
    ax_ratio.plot(use_midpoints, line_np(use_midpoints, (Fo4_values)), color="purple", label="4th order")

    print("FIT COEFFICIENTS")
    print(f"0th order: {Fo0_label}")
    print(f"1st order: {Fo1_label}")
    print(f"2nd order: {Fo2_label}")
    print(f"3rd order: {Fo3_label}")
    print(f"4th order: {Fo4_label}")

    spruce_up_single_plot(ax_ratio, label_dictionary[var], "Fake Factor Ratio and Fit", 
                          title, final_state_mode, jet_mode, yrange=[0.0, 1.0])
    plt.savefig(plot_dir + "/" + str(var) + "_" + str(region) + ".png")

  if hide_plots: pass
  else: plt.show()
  log_print(f"Finished plots for FF region!", log_file, time=True)


