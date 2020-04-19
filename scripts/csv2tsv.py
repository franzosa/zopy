#!/usr/bin/env python

import sys
import csv

writer = csv.writer( sys.stdout, csv.excel_tab )
for row in csv.reader( sys.stdin ):
    writer.writerow( row )
