#This file is a part of xboa
#
#xboa is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#xboa is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with xboa in the doc folder.  If not, see 
#<http://www.gnu.org/licenses/>.

"""
\namespace _opal_tracking
"""

import tempfile
import subprocess
import os
import glob

from xboa import common
from xboa.hit import Hit

from xboa.tracking import TrackingBase 

class OpalTracking(TrackingBase):
    """
    Provides an interface to OPAL tracking routines for use by xboa.algorithms
    """
    def __init__(self, lattice_filename, beam_filename, reference_hit, output_filename, opal_path, log_filename):
        """
        Initialise OpalTracking routines
        - lattice_filename is the Opal lattice file that OpalTracking will use
        - beam_filename is a filename that OpalTracking will overwrite when it
          runs the tracking, putting in beam data
        - reference_hit defines the centroid for the tracking; this should
          correspond to 0 0 0 0 0 0 in the beam file
        - output_filename the name of the PROBE file that OpalTracking will
          read to access output data; wildcards (*, ?) are allowed, in which
          case all files matching the wildcards will be loaded
        - opal_path path to the OPAL executable
        - allow_duplicate_station when evaluates to False, OpalTracking will
          discard duplicate stations on the same event
        - log_filename set to a string file name where OpalTracking will put the 
          terminal output from the opal command; if None, OpalTracking will make
          a temp file
        """
        self.beam_filename = beam_filename
        self.lattice_filename = lattice_filename
        self.output_name = output_filename
        self.opal_path = opal_path
        self.ref = reference_hit
        self.last = None
        self.allow_duplicate_station = False
        self.do_tracking = True
        self.log_filename = log_filename
        # clear any existing files (to prevent reloading "stale" files)
        for a_file in glob.glob(self.output_name):
            os.remove(a_file)

        
    def track_one(self, hit):
        """
        Track one hit through Opal

        Returns a list of hits, sorted by time.
        """
        return self.track_many([hit])[0]
        
    def track_many(self, list_of_hits):
        """
        Track many hits through Opal

        Returns a list of lists of hits; each list of hits corresponds to a
        track, defined by probe "id" field. Output hits are sorted by time 
        within each event.
        """
        if self.do_tracking:
            self._tracking(list_of_hits)
        hit_list_of_lists = self._read_probes()
        return hit_list_of_lists

    def _tracking(self, list_of_hits):
        if self.log_filename != None:
            log_file = open(self.log_filename, "w")
            fname = self.log_filename
        else:
            fname = tempfile.mkstemp()[1]
            print "Using logfile ", fname
            log_file = open(fname, 'w')
        open(self.lattice_filename).close() # check that lattice exists
        m, eV = common.units["m"], common.units["eV"]
        fout = open(self.beam_filename, "w")
        print >> fout, len(list_of_hits)
        for hit in list_of_hits:
            print 'tracking hit ...',
            for key in 'x', 'y', 'z', 'px', 'py', 'pz':
                print hit[key],
            print
            print '         ref ...',
            for key in 'x', 'y', 'z', 'px', 'py', 'pz':
                print self.ref[key],
            print
            x = (hit["x"]-self.ref["x"])/m
            y = (hit["y"]-self.ref["y"])/m
            z = (hit["z"]-self.ref["z"])/m
            px = hit["px"]-self.ref["px"]
            py = hit["pz"]-self.ref["pz"]
            pz = hit["py"]-self.ref["py"] # NOTE! Wrong Units
            print >> fout, x, px, z, pz, y, py
        fout.close()
        try:
            os.remove(self.output_name) # make sure we don't load an old PROBE file
        except OSError:
            pass
        proc = subprocess.Popen([self.opal_path, self.lattice_filename],
                                stdout=log_file,
                                stderr=subprocess.STDOUT)
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("OPAL quit with non-zero error code "+\
                               str(proc.returncode)+". Review the log file: "+\
                               str(fname))

    def _remove_duplicate_stations(self, list_of_hit_dicts):
        if self.allow_duplicate_station:
            return list_of_hit_dicts
        dict_of_hit_dicts = {} # temp mapping of station to hit_dict
        for hit_dict in list_of_hit_dicts:
            dict_of_hit_dicts[station] = hit_dict # overwrites if a duplicate
        return dict_of_hit_dicts.values() # list of hit dicts

    def _read_probes(self):
        hit_dict_of_lists = {} # maps event number to a list of hit_dicts
        # loop over files in the glob, read events and sort by event number
        file_list = glob.glob(self.output_name)
        for file_name in file_list:
            fin = open(file_name)
            fin.readline()
            # go through file line by line reading hit data
            for line in fin.readlines():
                words = line.split()
                hit_dict = {}
                for key in "pid", "mass", "charge":
                    hit_dict[key] = self.ref[key]
                for i, key in enumerate(["x", "z", "y"]):
                    hit_dict[key] = float(words[i+1])
                for i, key in enumerate(["px", "pz", "py"]):
                    hit_dict[key] = float(words[i+4])*self.ref["mass"]
                event = int(words[7])
                hit_dict["event_number"] = int(words[7])
                hit_dict["station"] = int(words[8])
                hit_dict["t"] = float(words[9])
                hit_dict["x"] = (hit_dict["x"]**2.+hit_dict["z"]**2.)**0.5
                hit_dict["z"] = 0.
                if not event in hit_dict_of_lists:
                    hit_dict_of_lists[event] = []
                hit_dict_of_lists[event].append(Hit.new_from_dict(hit_dict, "energy"))
        # convert from a dict of list of hits to a list of list of hits
        # one list per event
        # each list contains one hit per station
        events = sorted(hit_dict_of_lists.keys())
        hit_list_of_lists = [hit_dict_of_lists[ev] for ev in events]
        # sort by time within each event
        for i, hit_list in enumerate(hit_list_of_lists):
            hit_list_of_lists[i] = sorted(hit_list, key = lambda hit: hit['t'])        
        self.last = hit_list_of_lists
        return hit_list_of_lists


