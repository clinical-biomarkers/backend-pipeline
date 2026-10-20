import json
import myvariant

mv = myvariant.MyVariantInfo()
# Query the rsID
rsid = "rs1650697"
res = mv.getvariant(rsid, fields='dbsnp.gene')
for obj in res:
    for o in obj["dbsnp"]["gene"]:
        print (o["geneid"], o["name"])


