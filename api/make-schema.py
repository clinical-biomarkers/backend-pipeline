import sys,os
import json
import string
import glob
from genson import SchemaBuilder
from optparse import OptionParser


def main():

    usage = "\n%prog  [options]"
    parser = OptionParser(usage,version="%prog version___")
    parser.add_option("-i","--infile",action="store",dest="infile",help="")
    parser.add_option("-o","--outfile",action="store",dest="outfile",help="")
    
    (options,args) = parser.parse_args()
    for key in ([options.infile, options.outfile]):
        if not (key):
            parser.print_help()
            sys.exit(0)

    in_file = options.infile
    out_file = options.outfile
    in_obj = json.loads(open(in_file,"r").read())
    builder = SchemaBuilder()
    builder.add_object(in_obj)
    out_obj = builder.to_schema()
     
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(out_obj, indent=4)))
           
    return


if __name__ == '__main__':
    main()



