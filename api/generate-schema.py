from genson import SchemaBuilder
import json
import subprocess

def main():

    in_file = "/data/shared/biomarkerdb/tmp/AN6278-5.json"
    out_file = "/data/shared/biomarkerdb/tmp/AN6278-5.schema.json"

    data = json.load(open(in_file))
    
    builder = SchemaBuilder()
    builder.add_object(data)
    schema = builder.to_schema()
    
    with open(out_file, "w") as FW:
        FW.write("%s\n" % (json.dumps(schema, indent=4)))

    cmd = "chmod 775 /data/shared/biomarkerdb/tmp/AN6278-5*"
    x = subprocess.getoutput(cmd)
    
    print ("created schema file:%s" % (out_file))

    return

if __name__ == '__main__':
    main()


