# -*- coding: utf-8 -*-
# Load an espion export file
import parse_espion_export


fname = "../../samples/erg_protocol_1.2_version_6.64.14.txt"

if __name__ == "__main__":
    data = parse_espion_export.load_file(fname)

