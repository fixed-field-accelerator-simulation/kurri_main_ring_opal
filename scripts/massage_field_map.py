"""
Massage field map into the correct format
"""

def main():
    """Main function"""
    field_map_in = open("tosca_map_f810_d1020.table")
    for i in range(8):
        line = field_map_in.readline()
        print line,

    current_word = ''
    block = []
    for i, line in enumerate(field_map_in.readlines()):
        words = line.split()
        if words[1] == current_word:
            block.append(line)
        else:
            current_word = words[1]
            for line_out in reversed(block):
                print line_out,
            block = [line]

    for line_out in reversed(block):
        print line_out,

if __name__ == "__main__":
    main()

