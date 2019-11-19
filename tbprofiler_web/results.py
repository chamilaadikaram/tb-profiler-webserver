from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, Response
)
from werkzeug.exceptions import abort
import json
#from aseantb.auth import login_required
from tbprofiler_web.db import get_db
import tbprofiler as tbp

bp = Blueprint('results', __name__)


@bp.route('/results')
def result_table():
	db = get_db()
	tmp = db.execute("select * from results").fetchall()
	results = []
	for x in tmp:
		r = dict(x)
		r["result"] = json.loads(r["result"])
		results.append(r)
	return render_template('results/result_table.html',results=results[::-1])

@bp.route('/results/<uuid:sample_id>',methods=('GET', 'POST'))
def run_result(sample_id):
	db = get_db()
	tmp = db.execute("SELECT * FROM results WHERE id = ?", (str(sample_id),) ).fetchone()
	if tmp == None:
		error = "Run does not exists"
		abort(404)
	run = dict(tmp)
	run["result"] = json.loads(tmp["result"])
	if request.method == 'POST':
		json_results = run["result"]
		csv_strings = {}
		csv_strings["id"] = json_results["id"]
		csv_strings["date"] = run["created"]
		csv_strings["strain"] = json_results["sublin"]
		csv_strings["drtype"] = json_results["drtype"]
		csv_strings["dr_report"] = tbp.dict_list2csv(json_results["drug_table"],["Drug","Genotypic Resistance","Mutations"]+[])
		csv_strings["lineage_report"] = tbp.dict_list2csv(json_results["lineage"],["lin","frac","family","spoligotype","rd"],{"lin":"Lineage","frac":"Estimated fraction"})
		csv_strings["other_var_report"] = tbp.dict_list2csv(json_results["other_variants"],["genome_pos","locus_tag","change","freq"],{"genome_pos":"Genome Position","locus_tag":"Locus Tag","freq":"Estimated fraction"})
		csv_strings["pipeline"] = tbp.dict_list2csv(json_results["pipline_table"],["Analysis","Program"])
		csv_strings["version"] = json_results["tbprofiler_version"]
		csv_strings["db_version"] = json_results["db_version"]
		csv = tbp.load_csv(csv_strings)
		return Response(csv,mimetype="text/csv",headers={"Content-disposition": "attachment; filename=%s.csv" % sample_id})
	return render_template('results/run_result.html',run=run)
