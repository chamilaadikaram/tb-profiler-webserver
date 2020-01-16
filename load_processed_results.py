import sys
import argparse
import sqlite3
import os
from tqdm import tqdm
import uuid
import json
import tbprofiler as tbp
import pathogenprofiler as pp
try:
	sys.base_prefix
except:
	sys.base_prefix = getattr(sys, 'base_prefix', getattr(sys, 'real_prefix', sys.prefix))

def get_conf_dict(library_prefix):
	files = {"gff":".gff","ref":".fasta","ann":".ann.txt","barcode":".barcode.bed","bed":".bed","json_db":".dr.json","version":".version.json"}
	conf = {}
	for key in files:
		sys.stderr.write("Using %s file: %s\n" % (key,library_prefix+files[key]))
		conf[key] = pp.filecheck(library_prefix+files[key])
	return conf

def main(args):
	drug_order = ["isoniazid","rifampicin","ethambutol","pyrazinamide","streptomycin","ethionamide","moxifloxacin","ofloxacin","levofloxacin","ciprofloxacin","fluoroquinolones","amikacin","capreomycin","kanamycin","aminoglycosides","para_aminosalicylic_acid","cycloserine","linezolid","bedaquiline","clofazimine","delamanid"]
	conf = get_conf_dict(sys.base_prefix+"/share/tbprofiler/tbdb")
	samples = [x.replace(".results.json","") for x in os.listdir(args.dir) if x[-13:]==".results.json"]
	db = sqlite3.connect(args.sql_db)
	c = db.cursor()
	for s in tqdm(samples):
		uniq_id = str(uuid.uuid4())
		f = "%s/%s.results.json" % (args.dir,s)
		tmp = json.load(open(f))
		tmp = tbp.get_summary(tmp,conf,drug_order=drug_order)
		if "db_version" not in tmp:
			tmp["db_version"] = {}
		# print(open(f).readline())
		c.execute("INSERT INTO results (id,user_id,sample_name,status,result,lineage,drtype) VALUES (?,?,?,?,?,?,?)",(uniq_id,"public",s,"completed",json.dumps(tmp),tmp["sublin"],tmp["drtype"]))
		c.execute("INSERT INTO full_results (id,sample_name,main_lineage,sub_lineage,DR_type,MDR,XDR) VALUES (?,?,?,?,?,?,?)",(uniq_id,s,tmp["main_lin"],tmp["sublin"],tmp["drtype"],tmp["MDR"],tmp["XDR"]))
		for d in tmp["drug_table"]:
			c.execute("UPDATE full_results SET %s = ? where id = ?" % d["Drug"].lower().replace("-","_"), (d["Mutations"],uniq_id,))

	db.commit()




parser = argparse.ArgumentParser(description='TBProfiler pipeline',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--sql-db',type=str,help='NGS Platform',required=True)
parser.add_argument('--dir',default="results/",type=str,help='NGS Platform')
parser.set_defaults(func=main)

args = parser.parse_args()
args.func(args)
