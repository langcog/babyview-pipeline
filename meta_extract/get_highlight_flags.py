"""
GoPro Highlight Parser:  https://github.com/icegoogles/GoPro-Highlight-Parser

The code for extracting the mp4 boxes/atoms is from 'Human Analog' (https://www.kaggle.com/humananalog): 
https://www.kaggle.com/humananalog/examine-mp4-files-with-python-only

"""

import os, sys
import struct
import numpy as np
from math import floor


def find_boxes(f, start_offset=0, end_offset=float("inf")):
    """Returns a dictionary of all the data boxes and their absolute starting
    and ending offsets inside the mp4 file.

    Specify a start_offset and end_offset to read sub-boxes.
    """
    s = struct.Struct("> I 4s") 
    boxes = {}
    offset = start_offset
    f.seek(offset, 0)
    while offset < end_offset:
        data = f.read(8)               # read box header
        if data == b"": break          # EOF
        length, text = s.unpack(data)
        f.seek(length - 8, 1)          # skip to next box
        boxes[text] = (offset, offset + length)
        offset += length
    return boxes

def examine_mp4(filename):
        
    with open(filename, "rb") as f:
        boxes = find_boxes(f)

        # Sanity check that this really is a movie file.
        def fileerror():  # function to call if file is not a movie file
            print("")
            print("ERROR, file is not a mp4-video-file!")

            os.system("pause")
            exit()

        try:
            if boxes[b"ftyp"][0] != 0:
                fileerror()
        except:
            fileerror()


        moov_boxes = find_boxes(f, boxes[b"moov"][0] + 8, boxes[b"moov"][1])
       
        udta_boxes = find_boxes(f, moov_boxes[b"udta"][0] + 8, moov_boxes[b"udta"][1])

        ### get GPMF Box
        highlights = parse_highlights_HMMT(f, udta_boxes[b'GPMF'][0] + 8, udta_boxes[b'GPMF'][1])

        print("")
        print("Filename:", filename)
        print("Found", len(highlights), "Highlight(s)!")
        print('Here are all Highlights: ', highlights)

        return highlights

def parse_highlights_HMMT(f, start_offset=0, end_offset=float("inf")):
    listOfHighlights = []    
    f.seek(start_offset, 0)

    def read_highlight_and_append(f, list):
        data = f.read(4)
        if not data:  # EOF check
            return False
        timestamp = int.from_bytes(data, "big")
        if timestamp != 0:
            list.append(timestamp)
        return True

    while f.tell() < end_offset:  # check to ensure within offset bounds
        data = f.read(4)               # read box header
        if not data:  # EOF check
            break
        if data == b"HMMT":
            data = f.read(4)
            if not data:  # EOF check
                break
            num_highlights = int.from_bytes(data, "big")
            for _ in range(num_highlights):
                if not read_highlight_and_append(f, listOfHighlights):
                    break  # Exit if EOF encountered during highlights read
            break

    return np.array(listOfHighlights)/1000  # convert to seconds and return

def sec2dtime(secs):
    """converts seconds to datetimeformat"""
    milsec = (secs - floor(secs)) * 1000
    secs = secs % (24 * 3600) 
    hour = secs // 3600
    secs %= 3600
    min = secs // 60
    secs %= 60
      
    return "%d:%02d:%02d.%03d" % (hour, min, secs, milsec) 



# Main
if __name__ == '__main__':

    # //////////////
    filename = None  # You can enter a custom filename here istead of 'None'. Otherwise just drag and drop a file on this script
    # //////////////



    if filename is None:

        fNames = []

        try:
            counter = 1
            while True:
                try:
                    fNames.append(sys.argv[counter])
                except IndexError:
                    if counter > 1:  # at least one file found
                        break
                    else:
                        _ = sys.argv[counter]  # no file found => create IndexError
                counter += 1

        except IndexError:
            # Print error and exit after next userinput
            print(("\nERROR: No file selected. Please drag the chosen file onto this script to parse for highlights.\n" + 
                "\tOr change \"filename = None\" with the filename in the sourcecode."))
            os.system("pause")
            exit()
    else:
        fNames = [filename]
    

    str2insert = ""

    for fName in fNames:  

        str2insert += fName + "\n"

        highlights = examine_mp4(fName)  # examine each file

        highlights.sort()

        for i, highl in enumerate(highlights):
            str2insert += "(" + str(i+1) + "): "
            str2insert += sec2dtime(highl) + "\n"

        str2insert += "\n"

    # Create document
    stripPath, _ = os.path.splitext(fNames[0])
    outpFold, newFName = os.path.split(stripPath)

    newPath = os.path.join(outpFold, 'GP-Highlights_' + newFName + '.txt')

    with open(newPath, "w") as f:
        f.write(str2insert)

    print("Saved Highlights under: \"" + newPath + "\"")
