"""
Massage field map into the correct format
"""

import math

def cylindrical_to_cartesian(r, phi, axis):
    x = r*math.cos(phi)
    z = r*math.sin(phi)
    y = axis
    return (x, y, z)

def print_block(block):
    for line_out in reversed(block):
        words = line_out.split()
        r = float(words[0])
        phi = float(words[1])
        axis = float(words[2])
        phi = abs(phi-math.pi/2.)
        x, y, z = cylindrical_to_cartesian(r, phi, axis)
        #if abs(r-390.) < 0.1 and abs(axis-0.1) < 0.01:
        print x, y, z, words[3], words[4], float(words[5])
    # QUERY - SHOULD BZ BE NEGATIVE AFTER SYMMETRY POINT
    for line_out in block[1:]:
        words = line_out.split()
        r = float(words[0])
        phi = float(words[1])
        axis = float(words[2])       
        phi = -abs(phi-math.pi/2.)
        x, y, z = cylindrical_to_cartesian(r, phi, axis)
        #if abs(r-390.) < 0.1 and abs(axis-0.1) < 0.01:
        print x, y, z, words[3], words[4], -float(words[5])

def main():
    """Main function"""
    field_map_in = open("fieldmaps/TOSCA_cyli13.H")
    for i in range(8):
        line = field_map_in.readline()
        print line,

    current_word = None
    block = []
    while True:
        line = field_map_in.readline()
        words = line.split()
        if current_word == None:
            current_word = words[2]
        if len(words) > 1 and words[2] == current_word: # still in same vertical step
            block.append(line)
        else: # new vertical step
            print_block(block)
            if line == '':
                break
            current_word = words[2] # vertical step
            block = [line]

if __name__ == "__main__":
    main()

