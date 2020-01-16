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
def tbprofiler(fq1,fq2,uniq_id,db,storage_dir,platform):
    conf = get_conf_dict(sys.base_prefix+"/share/tbprofiler/tbdb")
    drug_order = ["isoniazid","rifampicin","ethambutol","pyrazinamide","streptomycin","ethionamide","fluoroquinolones","amikacin","capreomycin","kanamycin"]

    if fq1 and fq2:
        fastq_obj = pp.fastq(fq1,fq2)
    elif fq1 and fq2==None:
        fastq_obj = pp.fastq(fq1)
    files_prefix = storage_dir+"/"+uniq_id
    bam_obj = fastq_obj.map_to_ref(
        ref_file=conf["ref"], prefix=files_prefix,sample_name=uniq_id,
        aligner="bwa", platform=platform, threads=4
    )
    bam_file = bam_obj.bam_file

    results = pp.bam_profiler(
        conf=conf, bam_file=bam_file, prefix=files_prefix, platform=platform,
        caller="bcftools", threads=4, no_flagstat=False,
        run_delly = True
    )

    results = tbp.reformat(results, conf, reporting_af=0.1)

    results["id"] = uniq_id
    results["tbprofiler_version"] = tbp._VERSION
    results["pipeline"] = {"mapper":"bcftools","variant_caller":"bcftools"}
    results = tbp.get_summary(results,conf,drug_order=drug_order)
    outfile = "%s.results.json" % (storage_dir+"/"+uniq_id)

    json.dump(results,open(outfile,"w"))



    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("UPDATE results SET result = ?, lineage = ?, drtype = ?, status = 'completed' where id = ?", (open(outfile).readline(),results["sublin"],results["drtype"],uniq_id,))
    c.execute("UPDATE full_results SET main_lineage = ?, sub_lineage = ?, DR_type = ?, MDR = ?, XDR = ?",(results["main_lin"],results["sublin"],results["drtype"],results["MDR"],results["XDR"]))
    for d in results["drug_table"]:
        c.execute("UPDATE full_results SET %s = ? where id = ?" % d["Drug"].lower().replace("-","_"), (d["Mutations"],uniq_id,))
    conn.commit()
    pp.run_cmd("rm %s/%s*" % (storage_dir,uniq_id))

    return True
