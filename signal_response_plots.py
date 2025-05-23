# Authored by Braden Allmond, Sep 11, 2023
DEBUG = False

# libraries
import numpy as np
import sys
import matplotlib.pyplot as plt
import gc
import copy

# explicitly import used functions from user files, grouped roughly by call order and relatedness
# import statements for setup
from setup               import setup_handler, set_good_events
from branch_functions    import set_branches
from plotting_functions  import set_vars_to_plot
from file_map_dictionary import set_dataset_info

# import statements for data loading and processing
from file_functions          import load_process_from_file, append_to_combined_processes, sort_combined_processes
from FF_functions            import set_JetFakes_process, FF_control_flow
from cut_and_study_functions import apply_HTT_FS_cuts_to_process
from cut_and_study_functions import apply_cut, set_protected_branches

# plotting
from luminosity_dictionary import luminosities_with_normtag as luminosities
from plotting_functions    import get_midpoints, make_eta_phi_plot
from plotting_functions    import get_binned_data, get_binned_backgrounds, get_binned_signals, get_summed_backgrounds
from plotting_functions    import setup_ratio_plot, make_ratio_plot, spruce_up_plot, spruce_up_legend
from plotting_functions    import spruce_up_single_plot, add_text
from plotting_functions    import plot_raw, plot_data, plot_MC, plot_signal, make_bins, make_pie_chart, make_two_dimensional_plot
from plotting_functions    import make_two_dimensional_ratio_plot
from plotting_functions    import setup_unrolled_plot, spruce_up_unrolled_plot
from binning_dictionary    import label_dictionary

from calculate_functions   import calculate_signal_background_ratio, yields_for_CSV
from utility_functions     import time_print, make_directory, print_setup_info, log_print, print_processing_info

from make_fitter_shapes    import save_fitter_shapes

def make_masks_per_bin(input_dictionary, var, binning):
  passing_var_bins_dict = {}
  for process in input_dictionary.keys():
    passing_var_bins = []
    input_array = input_dictionary[process]["PlotEvents"][var]
    for i in range(len(binning)):
      if (i != len(binning) - 1):
        premask1 = input_array >= binning[i]
        premask2 = input_array < binning[i+1]
        mask = np.logical_and(premask1, premask2)
      else:
        mask = input_array >= binning[i]
      passing_var_bins.append(mask)
    passing_var_bins_dict[process] = passing_var_bins
  return passing_var_bins_dict # dictionary of list of masks


if __name__ == "__main__":
  # do setup
  setup = setup_handler()
  testing, final_state_mode, jet_mode, era, lumi, tau_pt_cut = setup.state_info
  using_directory, plot_dir, log_file, use_NLO, file_map, one_file_at_a_time, temp_version = setup.file_info
  hide_plots, hide_yields, DeepTau_version, do_JetFakes, semilep_mode, _, presentation_mode = setup.misc_info
  if one_file_at_a_time: import glob

  print_setup_info(setup)
  # used for printing, might be different from what is called per process
  good_events  = set_good_events(final_state_mode, era, non_SR_region=False, temp_version=temp_version)
  branches     = set_branches(final_state_mode, era, DeepTau_version, "ggH_TauTau", temp_version=temp_version)
  vars_to_plot = set_vars_to_plot(final_state_mode, jet_mode=jet_mode)
  from branch_functions import add_signal_branches
  vars_to_plot = add_signal_branches(vars_to_plot)
  print_processing_info(good_events, branches, vars_to_plot, log_file)

  _, reject_datasets = set_dataset_info(final_state_mode)

  #signal_processes = ["ggH_TauTau", "VBF_TauTau"]
  signal_processes = ["ggH_TauTau"]

  # make and apply cuts to any loaded events, store in new dictionaries for plotting
  combined_process_dictionary = {}
  for process in file_map: 

    if (process not in signal_processes): continue

    # being reset each run, but they're literally strings so who cares
    branches     = set_branches(final_state_mode, era, DeepTau_version, process, temp_version=temp_version)

    # This line skips Muon_Run* when processing the ditau final state, for example 
    if (process in reject_datasets): continue

    if not one_file_at_a_time:
      # One single entry per process, probably containing wildcard symbol, as defined in file_map_dictionary.py
      input_files = [file_map[process]]
    else:
      # Multiple entries per process, results from wildcard search
      input_files = glob.glob( using_directory + "/" + file_map[process] + ".root")
      input_files = sorted([f.replace(using_directory+"/","")[:-5] for f in input_files])

    for input_file in input_files:
      this_file_map = {process: input_file} # Make a temporary filemap just for this loop
      new_process_dictionary = load_process_from_file(process, using_directory, this_file_map, log_file,
                                                branches, good_events, final_state_mode,
                                                data=("Data" in process), testing=testing)
      if new_process_dictionary == None: continue # skip process if empty

      cut_events = apply_HTT_FS_cuts_to_process(era, process, new_process_dictionary, log_file, final_state_mode, jet_mode,
                                                DeepTau_version, tau_pt_cut)

      if cut_events == None: continue

      if ("DY" in process) and (final_state_mode != "dimuon"):
        # def split_DY_by_gen, return combined_process_dictionary
        event_flavor_arr = cut_events["event_flavor"]
        pass_gen_flav, pass_lep_flav, pass_jet_flav = [], [], []
        for i, event_flavor in enumerate(event_flavor_arr):
          if event_flavor == "G": pass_gen_flav.append(i)
          if event_flavor == "L": pass_lep_flav.append(i)
          if event_flavor == "J": pass_jet_flav.append(i)
    
        protected_branches = set_protected_branches(final_state_mode="none", jet_mode="Inclusive")
        background_gen_deepcopy = copy.deepcopy(cut_events)
        background_gen_deepcopy["pass_flavor_cut"] = np.array(pass_gen_flav)
        background_gen_deepcopy = apply_cut(background_gen_deepcopy, "pass_flavor_cut", protected_branches)
        if background_gen_deepcopy == None: continue

        background_lep_deepcopy = copy.deepcopy(cut_events)
        background_lep_deepcopy["pass_flavor_cut"] = np.array(pass_lep_flav)
        background_lep_deepcopy = apply_cut(background_lep_deepcopy, "pass_flavor_cut", protected_branches)
        if background_lep_deepcopy == None: continue

        background_jet_deepcopy = copy.deepcopy(cut_events)
        background_jet_deepcopy["pass_flavor_cut"] = np.array(pass_jet_flav)
        background_jet_deepcopy = apply_cut(background_jet_deepcopy, "pass_flavor_cut", protected_branches)
        if background_jet_deepcopy == None: continue

        if ("NLO" in process): process += "temp"
        combined_process_dictionary = append_to_combined_processes(process.replace("temp","DYGen"), background_gen_deepcopy, 
                                             vars_to_plot, combined_process_dictionary, one_file_at_a_time)
        combined_process_dictionary = append_to_combined_processes(process.replace("temp","DYLep"), background_lep_deepcopy, 
                                             vars_to_plot, combined_process_dictionary, one_file_at_a_time)
        combined_process_dictionary = append_to_combined_processes(process.replace("temp","DYJet"), background_jet_deepcopy, 
                                             vars_to_plot, combined_process_dictionary, one_file_at_a_time)
      else:
        combined_process_dictionary = append_to_combined_processes(process, cut_events, vars_to_plot, 
                                                                   combined_process_dictionary, one_file_at_a_time)
      del new_process_dictionary
      del cut_events
      gc.collect()

  # after loop, sort big dictionary into three smaller ones
  data_dictionary, background_dictionary, signal_dictionary = sort_combined_processes(combined_process_dictionary)

  # reversed dictionary search for era name based on lumi 
  title_era = [key for key in luminosities.items() if key[1] == lumi][0][0]
  title = f"{title_era}, {lumi:.2f}" + r"$fb^{-1}$"

  _, ax_h_compare = plt.subplots()
  _, ax_normed_diff = plt.subplots()
  _, ax_normed_diff_unrolled = plt.subplots()
  _, ax_raw_ratio = plt.subplots()
  _, ax_binned_ratio = plt.subplots()
  _, ax_normed_corr = plt.subplots()
  process_colors = {"ggH_TauTau" : "blue", "VBF_TauTau" : "red"}
  process_labels = {"ggH_TauTau" : "ggH", "VBF_TauTau" : "qqH"}
  bin_colors = ["green", "pink", "purple", "orange", "grey", "brown", "olive", "cyan","#00FF0F0F",
                "#A52A2A", "#8F00FF", "#90EE90"]
  #bin_colors = ["black", "red", "blue", "green", "pink", "purple", "orange", "grey", "brown", "olive", "cyan","#00FF0F0F"]
  marker_list = ["o", "v", "s", "*", "P", "d", "p", "o", "v", "s", "*", "P", "d", "p"]
  marker_face = ["full"]*7 + ["none"]*7
  for process in signal_processes: 
    # 1D plot 
    xbins = make_bins("HTT_H_pt", final_state_mode)
    #binning = np.array([0, 45, 80, 120, 200, 350, 450, 600])
    binning = np.array([0, 10, 20, 30, 40, 60, 80, 120, 200, 350, 450, 600])

    do_standard_comparison = False
    if (do_standard_comparison == True):
      h_signal_reco = get_binned_signals(final_state_mode, testing, signal_dictionary, "HTT_H_pt", xbins, lumi) 
      h_signal_gen  = get_binned_signals(final_state_mode, testing, signal_dictionary, "Gen_H_pT", xbins, lumi) 
      reco = h_signal_reco[process]["BinnedEvents"]
      gen  = h_signal_gen[process]["BinnedEvents"]
      # standard comparison
      plot_raw(ax_h_compare, xbins, reco, show_errors=True,
                        color=process_colors[process], label=f"{process_labels[process]} Reco", marker="v")
      plot_raw(ax_h_compare, xbins, gen, show_errors=True,
                        color=process_colors[process], label=f"{process_labels[process]} Gen", fillstyle="none")
      # ratio plot
      #plot_raw(ax_h_compare, xbins, gen/reco, show_errors=True,
      #                  color=process_colors[process], label=f"{process_labels[process]} Ratio (Gen/Reco)", fillstyle="none")

      spruce_up_single_plot(ax_h_compare, "H_pT", "Events", title, final_state_mode, jet_mode)

    raw_gen  = signal_dictionary[process]["PlotEvents"]["Gen_H_pT"]
    raw_reco = signal_dictionary[process]["PlotEvents"]["HTT_H_pt"]
    #mask = raw_reco > 200
    #raw_gen = raw_gen[mask]
    #raw_reco = raw_reco[mask]

    do_peak_corrections = False
    if (do_peak_corrections):
      # plot Reco with lines at bin boundaries + black point at max in each bin
      _, ax_c_reco = plt.subplots()
      fine_binning = np.linspace(0, binning[-1], 120+1) # 5 GeV bins
      raw_reco_fine, fine_bins = np.histogram(raw_reco, fine_binning)
      xdata_c_reco, ydata_c_reco = plot_raw(ax_c_reco, fine_binning, raw_reco_fine, show_errors=True,
               color=process_colors[process], label=f"{process_labels[process]} Reco", marker="v")
      ax_c_reco.vlines(binning, 0, ax_c_reco.get_ylim()[-1], linestyle="--", color="grey")

      max_vals_reco = []
      max_val_locs_reco = []
      #for i in range(len(binning)): # should really make this into a function :)
      for i in range(len(binning)-1): # should really make this into a function :)
        if (i != len(binning) - 1):
          mask = np.logical_and(xdata_c_reco >= binning[i], xdata_c_reco < binning[i+1])
          #mask = np.logical_and(raw_reco >= binning[i], raw_reco < binning[i+1])
          #mask = np.logical_and(raw_gen >= binning[i], raw_gen < binning[i+1])
        #else:
        #  mask = xdata_c_reco >= binning[i]
        #  mask = -1
          #mask = raw_reco >= binning[i]
          #mask = raw_gen >= binning[i]
        #print(ydata_c_reco[mask])
        max_val = max(ydata_c_reco[mask])
        all_loc = np.where(ydata_c_reco == max_val)
        loc = all_loc[0][-1] 
        max_vals_reco.append(max_val)
        max_val_locs_reco.append(xdata_c_reco[loc])

      max_vals_reco = np.array(max_vals_reco)
      max_val_locs_reco = np.array(max_val_locs_reco)
      ax_c_reco.errorbar(max_val_locs_reco, max_vals_reco,
                          color="black", marker="*", label = "Max Value",
                          linestyle='none', markersize=10)
      spruce_up_single_plot(ax_c_reco, "Reco H_pT", "Events", title, final_state_mode, jet_mode)
      ax_c_reco.set_ylim(0, None)

      # plot Gen from each Reco bin + point at max in each bin
      max_vals_gen = []
      max_val_locs_gen = []
      _, ax_c_gen = plt.subplots()
      for i in range(len(binning)-1):
        if (i != len(binning) - 1):
          mask = np.logical_and(raw_reco >= binning[i], raw_reco < binning[i+1])
          #mask = np.logical_and(raw_gen >= binning[i], raw_gen < binning[i+1])
          label_i = f"[{binning[i]} - {binning[i+1]}]"
        #else: # don't do final bin
        #  mask = raw_reco >= binning[i]
        #  #mask = raw_gen >= binning[i]
        #  label_i = f"[>{binning[i]}]"

        raw_gen_hist, _ = np.histogram(raw_gen[mask], fine_binning)

        xdata_c_gen, ydata_c_gen = plot_raw(ax_c_gen, fine_binning, raw_gen_hist, show_errors=True,
                          color=bin_colors[i], label=f"{process_labels[process]} {label_i}")

        max_gen = max(ydata_c_gen)
        all_locs = np.where(ydata_c_gen == max_gen)
        loc = all_locs[0][-1]
        max_vals_gen.append(max_gen)
        max_val_locs_gen.append(xdata_c_gen[loc])
      max_vals_gen = np.array(max_vals_gen)
      max_val_locs_gen = np.array(max_val_locs_gen)

      ax_c_gen.errorbar(max_val_locs_gen, max_vals_gen,
                          color="black", marker="*", label = "Max Value", markerfacecolor="none",
                          linestyle='none', markersize=10)

      spruce_up_single_plot(ax_c_gen, "Gen H_pT", "Events", title, final_state_mode, jet_mode)
      ax_c_gen.set_ylim(0, None)

      # plot ratio of max Gen / Reco (why is this better than an average?)
      # start by plotting them, then get the ratio
      # use process color, and filled/non filled

      _, ax_c_compare = plt.subplots()
      # plot points
      ax_c_compare.errorbar(max_val_locs_reco, max_vals_reco,
                          color=process_colors[process], label=f"{process_labels[process]}: Reco Peaks",
                          linestyle='none', marker='*', markersize=10)
      ax_c_compare.errorbar(max_val_locs_gen, max_vals_gen,
                          color=process_colors[process], label=f"{process_labels[process]}: Gen Peaks",
                          linestyle='none', marker='*', markersize=10, markerfacecolor="none")
      # plot lines connecting reco val to gen val 
      
      for i in range(len(max_val_locs_reco)):
      #for i in range(len(max_val_locs_gen)):
        ax_c_compare.plot([max_val_locs_reco[i],  max_val_locs_gen[i]], [max_vals_reco[i], max_vals_gen[i]], 
                          marker='none', color='grey', linestyle='dotted')
      spruce_up_single_plot(ax_c_compare, "H_pT", "Events (Max Values)", title, final_state_mode, jet_mode)
      ax_c_compare.set_ylim(0, None)

      _, ax_c_ratio = plt.subplots()
      ax_c_ratio.errorbar(binning[:-1], max_vals_reco/max_vals_gen,
                          color=process_colors[process], label=f"{process_labels[process]}",
                          linestyle="dashed", marker="o", markersize=10)
      spruce_up_single_plot(ax_c_ratio, "H_pT", "Correction (reco/gen peaks)", title, final_state_mode, jet_mode)
      ax_c_ratio.set_ylim(0, None)

    do_normed_diff_comparison = True
    reco_gen_normed_diffs = {}
    if (do_normed_diff_comparison):
      normed_gen_diff = (raw_reco-raw_gen)/raw_gen
      normed_gen_diff_bins = np.linspace(-2, 2, 100)

      normed_gen_diff_hist, _ = np.histogram(normed_gen_diff, normed_gen_diff_bins)
      normed_gen_diff_hist = normed_gen_diff_hist/np.max(normed_gen_diff_hist) # normed by highest yield

      plot_raw(ax_normed_diff, normed_gen_diff_bins, normed_gen_diff_hist, show_errors=True,
                         color=process_colors[process], label=process_labels[process])
      ax_normed_diff.vlines(0, 0, 1.1, linestyle="--", color="grey")

      spruce_up_single_plot(ax_normed_diff, "H_pT (Reco - Gen) / Gen", "Normalized Events", "Response", 
                            final_state_mode, jet_mode, yrange=[0.0, 1.1])

      # plot uncorrected normed_diff by binning region
      peaks = []
      bin_centers = []
      peak_locs = []
      for i in range(len(binning)):
        if (i != len(binning) - 1):
          mask = np.logical_and(raw_reco >= binning[i], raw_reco < binning[i+1])
          #mask = np.logical_and(raw_gen >= binning[i], raw_gen < binning[i+1])
          label_i = f"[{binning[i]} - {binning[i+1]}]"
        if (i == len(binning) - 1): continue
        #else:
        #  mask = raw_reco >= binning[i]
        #  #mask = raw_gen >= binning[i]
        #  label_i = f"[>{binning[i]}]"
        # apply mask to both and save result
        reco_gen_normed_diff = (raw_reco[mask] - raw_gen[mask])/raw_gen[mask]
        reco_gen_normed_diffs[binning[i]] = reco_gen_normed_diff

        reco_gen_normed_diff_hist, bin_edges = np.histogram(reco_gen_normed_diff, normed_gen_diff_bins)
        bin_size = bin_edges[2] - bin_edges[1]
        if (i != len(binning) - 1):
          binning_range = binning[i+1] - binning[i]
        reco_gen_normed_diff_hist = reco_gen_normed_diff_hist/np.max(reco_gen_normed_diff_hist) # normed by highest yield
        #reco_gen_normed_diff_hist = reco_gen_normed_diff_hist/np.sum(reco_gen_normed_diff_hist) # normed by sum
        #reco_gen_normed_diff_hist = reco_gen_normed_diff_hist/bin_size # divided by plot bin size
        #reco_gen_normed_diff_hist = reco_gen_normed_diff_hist/binning_range # normed by range of reco bin

        # store peak values
        peaks.append(max(reco_gen_normed_diff_hist))
        loc = np.where(reco_gen_normed_diff_hist == max(reco_gen_normed_diff_hist))[0][0]
        bin_val = bin_edges[loc] + (bin_edges[loc+1] - bin_edges[loc])/2
        peak_locs.append(bin_val)
        if (i != len(binning) - 1):
          bin_centers.append( binning[i] + (binning[i+1] - binning[i])/2 )
        else:
          bin_centers.append(binning[i])

        #if ((i == 0) or (i == 5)):
        if (True):
          plot_raw(ax_normed_diff_unrolled, normed_gen_diff_bins, reco_gen_normed_diff_hist, show_errors=False,
                            color=bin_colors[i], label=f"{process_labels[process]} {label_i}")
                          #alpha=(1 - i*0.1), marker=marker_list[i], fillstyle=marker_face[i])

      #spruce_up_single_plot(ax_normed_diff_unrolled, "H_pT (Reco - Gen) / Gen", "Normalized Events", "", 
      spruce_up_single_plot(ax_normed_diff_unrolled, "H_pT (Reco - Gen) / Gen", "Normalized Events", "", 
                            final_state_mode, jet_mode)
                            #final_state_mode, jet_mode, yrange=[0.0, 1.1])

      # plot peaks against bin centers
      peaks = np.array(peaks)
      bin_centers = np.array(bin_centers)
      inverts = np.array([1/(val+1) for val in peak_locs])
      inverts = np.append(inverts, inverts[-1]) # add last bin twice, so it's used for overflow

      invert_bin_index = np.digitize(raw_reco, binning) # documented in later lines
      corrected_raw_reco = raw_reco*inverts[invert_bin_index - 1]
      inverts = inverts[:-1] # remove last element (copy of second-to-last for overflow)
    
      # put your corrected values into the dictionary so you can use them anytime 
      signal_dictionary[process]["PlotEvents"]["HTT_H_pt_corr_Run2"] = np.array(corrected_raw_reco)
      
      _, ax_peaks = plt.subplots()
      ax_peaks.plot(bin_centers, peak_locs, linestyle="none", marker="o",
                    color=process_colors[process], label=process_labels[process])
      spruce_up_single_plot(ax_peaks, "H_pT", "xval at peak location", title, final_state_mode, jet_mode)

      _, ax_inverts = plt.subplots()
      ax_inverts.plot(bin_centers, inverts, linestyle="none", marker="o",
                      color=process_colors[process], label=process_labels[process])
      spruce_up_single_plot(ax_inverts, "H_pT", "Correction = 1/(xval+1)", title, final_state_mode, jet_mode)

      # 2D plot of reco val against the normalized generator difference
      fig, ax_2D = plt.subplots(figsize=(7,4))
      h2d, xbins, ybins = np.histogram2d(raw_reco, normed_gen_diff, bins=(xbins, normed_gen_diff_bins))
      h2d = h2d.T # transpose from image coordinates to data coordinates
      cmesh = ax_2D.pcolormesh(xbins, ybins, h2d, cmap="copper") #pcolormesh uses data coordinates by default, imshow uses array of 1x1 squares
      ax_2D.set_title(f"{final_state_mode} : {process}")
      ax_2D.set_xlabel("Reco H_pT")
      ax_2D.set_ylabel("H_pT (Reco - Gen) / Gen")
      plt.colorbar(cmesh)

      # raw value by value comparison
      raw_ratio = raw_reco/raw_gen
      #raw_ratio = raw_gen/raw_reco
      raw_ratio_bins = np.linspace(0, 5, 50+1)
      raw_ratio_hist, _ = np.histogram(raw_ratio, raw_ratio_bins)
      plot_raw(ax_raw_ratio, raw_ratio_bins, raw_ratio_hist, show_errors=True, 
                      color=process_colors[process], label=process_labels[process])
      spruce_up_single_plot(ax_raw_ratio, "H_pT Reco/Gen", "Events", "",
      #spruce_up_single_plot(ax_raw_ratio, "H_pT Gen/Reco", "Events", "",
                            final_state_mode, jet_mode)


    do_correction = True
    reco_gen_ratios = {}
    if (do_correction == True):
      for i in range(len(binning)):
        if (i != len(binning) - 1):
          mask = np.logical_and(raw_reco >= binning[i], raw_reco < binning[i+1])
          #mask = np.logical_and(raw_gen >= binning[i], raw_gen < binning[i+1])
        else:
          mask = raw_reco >= binning[i]
          #mask = raw_gen >= binning[i]
        # apply mask to both and save result
        #reco_gen_ratios[binning[i]] = np.mean(raw_reco[mask]) / np.mean(raw_gen[mask])
        reco_gen_ratios[binning[i]] = np.mean(raw_gen[mask]) / np.mean(raw_reco[mask])
        reco_gen_normed_diffs[binning[i]] = (raw_reco[mask] - raw_gen[mask])/raw_gen[mask]
      # plot binned correction values
      xvals = reco_gen_ratios.keys()
      yvals = reco_gen_ratios.values()
      ax_binned_ratio.plot(xvals, yvals, marker="o", linestyle="none",
                           color=process_colors[process], label=f"{process_labels[process]}")
      spruce_up_single_plot(ax_binned_ratio, "Reco H_pT", "Gen / Reco (Correction)", "",
      #spruce_up_single_plot(ax_binned_ratio, "Reco H_pT", "Reco / Gen (Correction)", "",
                            final_state_mode, jet_mode)

      # plot with correction applied
      reco_gen_ratio_vals = np.array(list(reco_gen_ratios.values()))
      ratio_bin_index = np.digitize(raw_reco, binning) # simply does exactly what you want..
      # digitize takes in a value and a binning and returns the index of the bin the value belongs to
      # you can use this index to then grab the associated correction
      corrected_raw_reco = raw_reco*reco_gen_ratio_vals[ratio_bin_index - 1]
    
      # put your corrected values into the dictionary so you can use them anytime 
      signal_dictionary[process]["PlotEvents"]["HTT_H_pt_corr"] = np.array(corrected_raw_reco)

      normed_corr_gen_diff = (corrected_raw_reco-raw_gen)/raw_gen
      normed_corr_gen_diff_bins = np.linspace(-2, 2, 100)

      normed_corr_gen_diff_hist, _ = np.histogram(normed_corr_gen_diff, normed_corr_gen_diff_bins)
      normed_corr_gen_diff_hist = normed_corr_gen_diff_hist/np.max(normed_corr_gen_diff_hist) # normed by highest yield

      plot_raw(ax_normed_corr, normed_corr_gen_diff_bins, normed_corr_gen_diff_hist, show_errors=True,
                         color=process_colors[process], label=process_labels[process])
      ax_normed_corr.vlines(0, 0, 1.1, linestyle="--", color="grey")

      spruce_up_single_plot(ax_normed_corr, "H_pT (Reco*Correction - Gen) / Gen", "Normalized Events", "Corrected Response", 
                            final_state_mode, jet_mode, yrange=[0.0, 1.1])
   
      # 2D plot of reco val against the normalized generator difference
      fig, ax_2D = plt.subplots(figsize=(7,4))
      h2d, xbins, ybins = np.histogram2d(raw_reco, normed_corr_gen_diff, bins=(xbins, normed_corr_gen_diff_bins))
      h2d = h2d.T # transpose from image coordinates to data coordinates
      cmesh = ax_2D.pcolormesh(xbins, ybins, h2d, cmap="copper") #pcolormesh uses data coordinates by default, imshow uses array of 1x1 squares
      ax_2D.set_title(f"{final_state_mode} : {process}")
      ax_2D.set_xlabel("Reco H_pT")
      ax_2D.set_ylabel("H_pT (Reco*Correction - Gen) / Gen")
      plt.colorbar(cmesh)

    
  plt.savefig("signal_response_plots/" + final_state_mode + "_H_pT_response.png", dpi=200)

  print(signal_dictionary.keys())
  do_response_plots = True
  if (do_response_plots):
    for process in signal_processes: 
      recoVars = ["HTT_H_pt_corr_Run2", "HTT_H_pt_corr", "HTT_H_pt", "nCleanJetGT30"]#, "CleanJetGT30_pt_1"]
      genVars  = ["Gen_H_pT", "Gen_H_pT", "Gen_H_pT", "Gen_nCleanJet"]#, "Gen_pT_j1"]
      varAltBins = [np.array([0, 45, 80, 120, 200, 350, 450, 600]), #H_pT
                    np.array([0, 45, 80, 120, 200, 350, 450, 600]), #H_pT
                    np.array([0, 45, 80, 120, 200, 350, 450, 600]), #H_pT
                    np.array([0, 1, 2, 3, 4])] # nJets
      norm_methods = ["row", "column"] # column shows reco smearing, row shows gen contribution to reco
      for norm_method in norm_methods:
        for bins, varY, varX in zip(varAltBins, recoVars, genVars):
          make_two_dimensional_plot(signal_dictionary[process]["PlotEvents"], final_state_mode,
                                    varX, varY, title=process + f" {norm_method} Unity Normalization Response",
                                    normalization = norm_method,
                                    alt_x_bins=bins, alt_y_bins=bins)
          name = "_".join([process, final_state_mode, norm_method, varX])
          plt.savefig("signal_response_plots/" + name + ".png", dpi=200)
  
  if hide_plots: pass
  else: plt.show()

