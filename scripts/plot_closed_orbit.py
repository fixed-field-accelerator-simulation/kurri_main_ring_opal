"""
Plot the closed orbit as a function of energy
"""

import sys
import json

import xboa.Common as common

def load_file():
    fin = open("output/find_closed_orbit.ref")
    data_out = {}
    for line in fin.readlines():
        one_data = json.loads(line)
        e_ref = one_data[0]
        if len(one_data) > 2 and abs(one_data[2][1]) < 1e-9:
            data_out[e_ref] = one_data[2:]
        elif len(one_data) > 1:
            data_out[e_ref] = one_data[1:]
        else:
            data_out[e_ref] = []
    print data_out.keys()
    return data_out

def plot_closed_orbit(data):
    print "\nclosed orbit",
    sys.stdout.flush()
    energy_list = [energy/1e3 for energy in data.keys()]
    x_list = [data[key][0][0] for key in data.keys()]
    canvas = common.make_root_canvas("closed orbit")
    hist, graph = common.make_root_graph("closed orbit", energy_list, "Kinetic Energy [GeV]", x_list, "Radial position [mm]")
    hist.Draw()
    graph.SetMarkerStyle(4)
    graph.Draw("p")
    graph.Fit("pol4")
    canvas.Update()
    canvas.Print("plots/closed_orbit.png")
    canvas.Print("plots/closed_orbit.root")
    

def _get_mean_tof(data):
    tof_list = [data[i+1][1]-data[i][1] for i, item in enumerate(data[1:])]
    tof_mean = sum(tof_list)/len(tof_list)
    return tof_mean

def plot_tof(data):
    print "\nfrequency",
    sys.stdout.flush()
    energy_list = [(energy-11.)/1e3 for energy in data.keys()]
    f_list = [1./_get_mean_tof(data[key]) for key in data.keys()]
    print f_list
    canvas = common.make_root_canvas("frequency")
    hist, graph = common.make_root_graph("frequency", energy_list, "Kinetic Energy [GeV]", f_list, "Frequency [GHz]")
    hist.Draw()
    graph.SetMarkerStyle(4)
    graph.Draw("p")
    graph.Fit("pol3")
    canvas.Update()

def main():
    data = load_file()
    plot_tof(data)
    plot_closed_orbit(data) 
    

if __name__ == "__main__":
    main()
    raw_input()
