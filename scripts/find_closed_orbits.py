"""
Script to find the tune; drives xboa EllipseClosedOrbitFinder algorithm
"""


import numpy
import sys
import os
import json
sys.path.insert(1, "scripts")
from opal_tracking import OpalTracking
import xboa.common as common
from xboa.hit import Hit
from xboa.algorithms.closed_orbit import EllipseClosedOrbitFinder

import ROOT

def reference(energy):
    """
    Generate a reference particle
    """
    hit_dict = {}
    hit_dict["pid"] = 2212
    hit_dict["mass"] = common.pdg_pid_to_mass[2212]
    hit_dict["charge"] = 1
    hit_dict["x"] = 4600.
    hit_dict["kinetic_energy"] = energy
    return Hit.new_from_dict(hit_dict, "pz")

def plot_iteration(i, iteration, energy, step, poly_order, smooth_order):
    """
    Plot the closed orbit ellipse and the ellipse fit
    """
    canvas, hist, graph, fit = iteration.plot_ellipse("x", "px", "mm", "MeV/c")
    hist.SetTitle('KE='+str(energy)+' iter='+str(i))
    canvas.Update()
    name = "plots/closed_orbit-i_"+str(i)+"-ke_"+str(energy)+"-step_"+str(step)+"-po_"+str(poly_order)+"-so_"+str(smooth_order)
    canvas.Print(name+".root")
    canvas.Print(name+".png")

def find_closed_orbit(energy, nturns, step, poly_order, smooth_order, seed):
    """
    Find the closed orbit; algorithm is to track turn by turn; fit an ellipse to
    the tracking; find the centre of the ellipse; repeat until no improvement or
    10 iterations.
    - energy: (float) kinetic energy at which the co is calculated
    - step: (float) step size in tracking
    - poly_order: (int) order of the polynomial fit to the field map (not used)
    - smooth_oder: (int) order of smoothing the polynomial fit to the field map
                   (not used)
    - seed: (list of 2 floats) [x, px] value to be used as the seed for the next 
            iteration; px value is ignored, sorry about that.
    """
    print "Energy", energy, "NTurns", nturns, "StepSize", step, "Seed", seed, "Poly Order", poly_order, "Smooth Order", smooth_order
    tmp_dir = "tmp/find_closed_orbits/"
    subs = {
        '__energy__':energy,
        '__stepsize__':step,
        '__nturns__':nturns,
        '__poly_order__':poly_order,
        '__smooth_order__':smooth_order,
        '__beamfile__':tmp_dir+'disttest.dat'
    }
    common.substitute('lattices/KurriMainRingTuneComparison/KurriMainRingTuneComparison.in', tmp_dir+'/Kurri_ADS_Ring.tmp', subs)
    ref_hit = reference(energy)
    opal_exe = os.path.expandvars("${OPAL_EXE_PATH}/opal")
    tracking = OpalTracking(tmp_dir+'/Kurri_ADS_Ring.tmp', tmp_dir+'/disttest.dat', ref_hit, 'PROBE*.loss', opal_exe, tmp_dir+"/log")
    mass = common.pdg_pid_to_mass[2212]
    seed_hit = ref_hit.deepcopy()
    seed_hit["x"] = seed[0]
    finder = EllipseClosedOrbitFinder(tracking, seed_hit)
    generator = finder.find_closed_orbit_generator(["x", "px"], 1)
    x_std_old = 1e9
    i = -1
    for i, iteration in enumerate(generator):
        print iteration.points
        print iteration.centre
        #if iteration.centre != None: #i == 0 and 
        if i == 0:
            plot_iteration(i, iteration, energy, step, poly_order, smooth_order)
        if i >= 10:
            break
        x_mean = numpy.mean([point[0] for point in iteration.points])
        x_std = numpy.std([point[0] for point in iteration.points])
        print "Seed:", iteration.points[0][0], "Mean:", x_mean, "Std:", x_std
        if iteration.centre != None and x_std >= x_std_old: # require convergence
            break
        x_std_old = x_std
    if i > -1:
        plot_iteration(i, iteration, energy, step, poly_order, smooth_order)

    return tracking.last[0]

if __name__ == "__main__":
      next_seed = [4411.02, 0., 0.] # [5154.51, 0.0] # 
      fout = open('find_closed_orbit.out', 'w')
      energy_list = range(11, 12, 1)
      for i, energy in enumerate(energy_list):
          is_batch = len(energy_list) > 5 and i > 4
          ROOT.gROOT.SetBatch(is_batch)
          hit_list = find_closed_orbit(energy, 5.1, 10, 1, 1, next_seed)
          next_seed = [hit_list[0]["x"], 0.]
          output = [energy]+[[hit["x"], hit["t"]] for hit in hit_list]
          print >> fout, json.dumps(output)
          fout.flush()
      if len(energy_list) < 5:
          print "Finished"
          raw_input()

