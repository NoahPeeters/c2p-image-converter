import argparse
import zlib
from c2p import *
from PIL import Image

parser = argparse.ArgumentParser(description='Convert images from and to the c2p format.')
parser.add_argument("inputFile", type=str, help="The input file.")
parser.add_argument("outputFile", type=str, help="The output file.")
parser.add_argument("-s", "--skipDimensionCheck", action="store_true", help="Skip the dimension check for the c2p file.")
parser.add_argument("-v", "--verbosity", action="count", help="Output verbosity.")
args = parser.parse_args()

if args.verbosity >= 3:
    print(args)

if args.verbosity >= 1:
    print("Open image '" + args.inputFile + "'.")

w = 1
h = 1
data = []

inputFileIsC2P = args.inputFile[-4:] == ".c2p"
outputFileIsC2P = args.outputFile[-4:] == ".c2p"

# Read file
if not inputFileIsC2P:
    # load normal image
    img = Image.open(args.inputFile).convert('RGB')
    w = img.size[0]
    h = img.size[1]
    data = list(img.getdata())
else:
    # load c2p image
    file = open(args.inputFile, 'rb')
    ba = bytearray(file.read())
    file.close()
    w = (ba[194] << 8) + ba[195]
    h = (ba[196] << 8) + ba[197]
    content = ba[HEADER_SIZE:-FOOTER_SIZE]

    decompressed_byte_data = zlib.decompress(content)

    for i in range(0, len(decompressed_byte_data), 2):
        rgb = (decompressed_byte_data[i] << 8) + decompressed_byte_data[i + 1]
        r = int(((rgb >> 11) & 0x1f) / 0x1f * 0xff)
        g = int(((rgb >> 5) & 0x3f) / 0x3f * 0xff)
        b = int((rgb & 0x1f) / 0x1f * 0xff)
        data.append((r, g, b))

# print image size
if args.verbosity >= 2:
    print("Image size: {}x{}".format(w, h))

# check errors
if w * h != len(data):
    print("Error while reading file. Pixel data size doesn't match image size.")
    exit(1)

if args.verbosity >= 1:
    print("Saving image '" + args.outputFile + "'.")

# saving image
if not outputFileIsC2P:
    img = Image.new("RGB", (w, h))
    img.putdata(data)
    img.save(args.outputFile)
else:
    if (not args.skipDimensionCheck) and (w > 0x136) or (h > 0x191):
        print(
            "This file is to big for the standard c2p format. The maximum size is 310x401. Use -s to skip this check."
            "Your calculate may not be able to read the file.")
        exit(2)

    rgb565 = []
    for i in range(0, len(data)):
        r = (data[i][0] >> 3) & 0x1F
        g = (data[i][1] >> 2) & 0x3F
        b = (data[i][2] >> 3) & 0x1F
        rgb = (r << 11) + (g << 5) + b
        rgb565.extend([rgb >> 8, rgb & 0xFF])

    compressed = zlib.compress(bytearray(rgb565))

    file_size = len(compressed) + HEADER_SIZE + FOOTER_SIZE
    result = bytearray(get_header(w, h, file_size)) + compressed + bytearray(
        get_footer())

    if args.verbosity >= 1:
        print("Resulting image size: " + str(file_size) + " bytes = " + str(round(file_size/1024, 1)) + " kbytes.")

    file = open(args.outputFile, "wb")
    file.write(result)
    file.close()
