import json
import numpy
import math
import xboa.common

def load_summary_data(filename, columns, units):
    fin = open(filename)
    fin.readline()
    zgoubi_data = []
    for line in fin.readlines():
        data = [float(word) for word in line.split()]
        for i, element in enumerate(data):
            data[i] = data[i]*xboa.common.units[units[i]]
        if len(data) != len(columns):
            print "Warning, data misaligned to columns"
            print "  ", columns
            print "  ", line
            print "  ", data
        new_dict = dict(zip(columns, data))
        zgoubi_data.append(new_dict)
    return zgoubi_data 

def load_json_file(filename):
    fin = open(filename)
    data = [json.loads(line) for line in fin.readlines()]
    return data

def make_summary_data(closed_orbits, cell_tunes, ring_tunes):
    all_data = {}
    for co in closed_orbits:
        summary_data_dict = {}
        mass = xboa.common.pdg_pid_to_mass[2212]
        kinetic_energy = co[0]
        energy = kinetic_energy+mass
        momentum = (energy**2.-mass**2.)**0.5
        position = co[1][0]
        turn_time = co[3][1]
        summary_data_dict["kinetic_energy"] = kinetic_energy
        summary_data_dict["p"] = momentum
        summary_data_dict["closed_orbit"] = position
        summary_data_dict["turn_time"] = turn_time
        summary_data_dict["cell_time"] = turn_time/12.
        speed = momentum/energy*xboa.common.constants["c_light"]
        summary_data_dict["mean_radius"] = turn_time*speed/math.pi/2.
        summary_data_dict["Qx"] = 0.
        summary_data_dict["Qy"] = 0.
        summary_data_dict["qx"] = 0.
        summary_data_dict["qy"] = 0.
        all_data[int(round(kinetic_energy))] = summary_data_dict
    try:
        for tune in ring_tunes:
            kinetic_energy = tune["energy"]
            summary_data_dict = all_data[int(round(kinetic_energy))]
            summary_data_dict["Qx"] = 4.-tune["x_tune"]
            summary_data_dict["Qy"] = 2.-tune["y_tune"]
            all_data[int(round(kinetic_energy))] = summary_data_dict
    except KeyError:
        pass
    try:
        for tune in cell_tunes:
            kinetic_energy = tune["energy"]
            summary_data_dict = all_data[int(round(kinetic_energy))]
            summary_data_dict["qx"] = tune["x_tune"]
            summary_data_dict["qy"] = 1.-tune["y_tune"]
            all_data[int(round(kinetic_energy))] = summary_data_dict
    except KeyError:
        pass
    data = all_data.values()
    data = sorted(data, key = lambda x: x["kinetic_energy"])
    print [dat["kinetic_energy"] for dat in data]
    return data

def write_summary_data(filename, columns, units, opal_data):
    fout = open(filename, "w")
    header = zip(columns, units)
    for col, unit in header:
        print >> fout, col, "["+unit+"]",
    print >> fout
    for a_dict in opal_data:
        for col in columns:
            print >> fout, a_dict[col],
        print >> fout
    

def main():
    columns = ["kinetic_energy", "p", "qx", "qy", "Qx", "Qy", "closed_orbit", "mean_radius", "cell_time", "turn_time"]
    units = ["MeV", "MeV/c", "", "", "", "", "m", "m", "mus", "mus"]
    zgoubi_data = load_summary_data("/home/cr67/MAUS/work/kurri/ads-ffag/maus/magnets_only/zgoubi_summary_tracking_data.dat", columns, units)
    closed_orbits = load_json_file("closed_orbits_all.ref")
    ring_tunes = load_json_file("ring_tunes_nturns=100.1_stepsize=10.0_poly_order=1_smooth_order=1_all.out")
    cell_tunes = []
    opal_data = make_summary_data(closed_orbits, cell_tunes, ring_tunes)
    for a_opal in opal_data:
        print a_opal
        for a_zgoubi in zgoubi_data:
            if abs(a_zgoubi["kinetic_energy"] - a_opal["kinetic_energy"]) < 0.1:
                print "zgoubi", [str(round(a_zgoubi[col], 3)).rjust(8) for col in columns]
                print "opal  ", [str(round(a_opal[col], 3)).rjust(8) for col in columns]
                print
    write_summary_data("opal_summary_data.dat", columns, units, opal_data)

if __name__ == "__main__":
    main()


