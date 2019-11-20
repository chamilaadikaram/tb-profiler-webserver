from celery import Celery
import subprocess
import json
import sqlite3
import pathogenprofiler as pp
import tbprofiler as tbp
import os
import sys
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

app = Celery('tasks', broker='pyamqp://guest@localhost//')


@app.task
def tbprofiler(fq1,fq2,uniq_id,sample_name,db,storage_dir):
	conf = get_conf_dict(sys.base_prefix+"/share/tbprofiler/tbdb")
	drug_order = ["isoniazid","rifampicin","ethambutol","pyrazinamide","streptomycin","ethionamide","fluoroquinolones","amikacin","capreomycin","kanamycin"]

	results = pp.profiler(conf=conf,prefix=storage_dir+"/"+sample_name,r1=fq1,r2=fq2,bam_file=None,call_method="low",min_depth=10,threads=3,platform="Illumina",mapper="bwa",run_delly=True)
	results = tbp.reformat(results,conf)
	results["id"] = sample_name
	results["tbprofiler_version"] = tbp._VERSION
	outfile = "%s.results.json" % (storage_dir+"/"+sample_name)
	results["pipeline"] = {"mapper":"bwa","variant_caller":"bcftools"}
	results = tbp.get_summary(results,conf,drug_order=drug_order)
	results["db_version"] = json.load(open(conf["version"]))
	json.dump(results,open(outfile,"w"))



	conn = sqlite3.connect(db)
	c = conn.cursor()
	c.execute("UPDATE results SET result = ?, lineage = ?, drtype = ?, status = 'completed' where id = ?", (open(storage_dir+"/"+sample_name+".results.json").readline(),results["sublin"],results["drtype"],uniq_id,))
	conn.commit()
	pp.run_cmd("rm %s/%s*" % (storage_dir,uniq_id))

	return True
