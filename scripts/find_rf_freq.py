"""Script to calculate RF frequency for a fixed accelerating phase"""

import bisect
import json
import math
import ROOT
import xboa.common

class FrequencyFinder(object):
    """
    Class to find frequency dependence of RF with time, for fixed reference
    voltage and phase.
    
    Time-of-flight around the ring is based on output from the closed orbit
    finder, with linear interpolation between points
    """
    def __init__(self, co_filename, energy_0, energy_1, voltage, phase):
        """
        Initialise the class
        - co_filename: name of the file containing the closed orbits (and source
          timing info)
        - energy_0: start energy for the frequency calculation
        - energy_1: final energy for the frequency calculation
        - voltage: fixed voltage with time
        - phase: fixed synchronous phase with time
        """
        self.energy_list = []
        self.time_list = []
        self.freq_list = []
        self.closed_orbits_t = {}
        self.closed_orbits_x = {}
        self._load_closed_orbits(co_filename)
        #self._test_get_a_freq()
        self.get_frequency(energy_0, energy_1, voltage, phase)

    def plot_frequency(self):
        """
        Plot the frequency with time; fit 4th order polynomial (to be fed into
        the RF polynomial_time_dependence)
        """
        canvas = xboa.common.make_root_canvas("frequency vs time")
        canvas.Draw()
        freq_list = [freq for freq in self.freq_list]
        hist, graph = xboa.common.make_root_graph("frequency vs time",
                                                  self.time_list, "time [ns]",
                                                  freq_list, "f [GHz]")
        hist.Draw()
        graph.Draw("sameL")
        fit = ROOT.TF1("fit", "pol4", 0, 20*1e6)
        fit.FixParameter(0, freq_list[0])
        graph.Fit(fit)
        canvas.Update()

    def get_frequency(self, energy_0, energy_1, voltage, phase):
        """
        Get the frequency
        - energy_0: start energy for the frequency calculation
        - energy_1: final energy for the frequency calculation
        - voltage: fixed voltage with time
        - phase: fixed synchronous phase with time
        Returns a tuple of (time_list, frequency_list)
        """
        energy = energy_0
        time_list = [0.]
        freq_list = [self._get_a_freq(energy)]
        
        while energy < energy_1:
            frequency = self._get_a_freq(energy)
            time = time_list[-1]+1./frequency
            time_list.append(time)
            freq_list.append(frequency)
            energy += voltage*math.sin(phase)
            #print energy, frequency, time
        print "Found frequencies for energy ", energy_0, "to", energy_1, "MeV"
        print "RF running with", voltage, "MV/turn and", \
              math.degrees(phase), "degrees"
        print "Start frequency", freq_list[0], "end", freq_list[-1], "GHz"
        print "For", len(time_list)-1, "turns and total cycle time", \
              time_list[-1], "ns"
        self.time_list = time_list
        self.freq_list = freq_list
        return time_list, freq_list

    def _get_a_freq(self, energy):
        """
        Get a RF frequency (1/time of flight) for energy using linear
        interpolation
        """
        left_index = bisect.bisect_left(self.energy_list, energy)
        if left_index+1 >= len(self.energy_list):
            left_index = len(self.energy_list)-2
        elif left_index > 0:
            left_index -= 1
        energy0 = self.energy_list[left_index]
        energy1 = self.energy_list[left_index+1]
        freq0 = 1./self.closed_orbits_t[energy0]
        freq1 = 1./self.closed_orbits_t[energy1]
        frequency = (freq1 - freq0)/(energy1-energy0)*(energy-energy0) + freq0
        #print "\nl:", left_index, "e0:", energy0, "e1:", energy1, \
        #      "f0:", freq0, "f1:", freq1, "DE:", energy-e0, "f", frequency
        return frequency

    def _test_get_a_freq(self):
        """Test the _get_a_freq function"""
        for i, energy_test in enumerate(self.energy_list):
            if i+1 < len(self.energy_list):
                energy = (self.energy_list[i+1]+self.energy_list[i])/2.
            else:
                energy = (-self.energy_list[i-1]+2.*self.energy_list[i])
            energy_test_2 = energy_test-1e-2
            print i, energy_test_2, self._get_a_freq(energy_test_2)
            print i, energy_test, self._get_a_freq(energy_test)
            energy_test_2 = energy_test+1e-2
            print i, energy_test_2, self._get_a_freq(energy_test_2)
            print i, energy_test, 1./self.closed_orbits_t[energy_test]
            print i, energy, self._get_a_freq(energy)
            print


    def _load_closed_orbits(self, filename):
        """Load closed orbits from a json file"""
        fin = open(filename)
        closed_orbits = [json.loads(line) for line in fin.readlines()]
        self._get_x(closed_orbits)
        self._get_t(closed_orbits)
        self.energy_list = sorted(self.closed_orbits_t.keys())

    def _get_x(self, closed_orbits):
        """Load the position info from the closed orbit data"""
        closed_orbits_energy = [orbit[0] for orbit in closed_orbits]
        closed_orbits_x = [orbit[1:][0][0] for orbit in closed_orbits]
        closed_orbits_x_dict = dict(zip(closed_orbits_energy, closed_orbits_x))
        self.closed_orbits_x = closed_orbits_x_dict

    def _get_t(self, closed_orbits):
        """Load the time info from the closed orbit data"""
        self.closed_orbits_t = {}
        for orbit in closed_orbits:
            delta_t = orbit[1:][-1][1] - orbit[1:][0][1]
            mean_t = delta_t/(len(orbit[1:])-1)
            energy = orbit[0]
            self.closed_orbits_t[energy] = mean_t

def main():
    """Main function"""
    finder = FrequencyFinder(
                  "lattices/KurriMainRingTuneComparison/closed_orbits.ref",
                  11., 150., 4.e-3, math.radians(30),
             )
    finder.plot_frequency()
    raw_input()

if __name__ == "__main__":
    main()

