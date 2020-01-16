from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, Response
)
from werkzeug.exceptions import abort
import json
from tbprofiler_web.auth import login_required
from tbprofiler_web.db import get_db
import tbprofiler as tbp
bp = Blueprint('results', __name__)



@bp.route('/results/<uuid:sample_id>',methods=('GET', 'POST'))
def run_result(sample_id):
	db = get_db()
	tmp = db.execute("SELECT * FROM results WHERE id = ?", (str(sample_id),) ).fetchone()
	if tmp == None:
		error = "Run does not exist"
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
		csv_text = tbp.load_csv(csv_strings)
		return Response(csv_text,mimetype="text/csv",headers={"Content-disposition": "attachment; filename=%s.csv" % sample_id})
	return render_template('results/run_result.html',run=run)





@bp.route('/sra',methods=('GET', 'POST'))
def sra():
	return result_table(request,"public")


def result_table(request,user):
	db = get_db()
	if request.method=='POST':
		if "search_strains_button" in request.form:
			sql_query = "select id,sample_name,created,status,lineage,drtype from results WHERE user_id = '%s'" % user
			filters = []
			key_values = list(request.form.lists())
			for key,values in list(request.form.lists()):
				if values==[""]:
					continue
				elif key=="sample_name":
					filters.append("( %s )" % (" OR ".join(["sample_name = '%s'" % (run_id.strip()) for run_id in values[0].split(",")])))
				elif key=="project_id":
					pass
					# filters.append("( %s )" % (" OR ".join(["project_id = '%s'" % (run_id.strip()) for run_id in values[0].split(",")])))
				elif key=="drtype":
					filters.append("( %s )" % (" OR ".join(["drtype = '%s'" % (drtype) for drtype in values])))
				elif key=="lineage":
					filters.append("( %s )" % (" OR ".join(["lineage LIKE '%s%%'" % (lineage.strip()) for lineage in values[0].split(",")])))
				else:
					pass

			if len(filters)>0:
				sql_query = sql_query + " AND %s" % (" AND ".join(filters))
			tmp = db.execute(sql_query).fetchall()
			return render_template('results/result_table.html',results = tmp, user=user)
		else:
			# print(request.form)
			if request.form["button"]=="download":
				ids = list(json.loads(request.form["ids"]).keys())
				cmd = "select * from full_results where id in ( %s )" % ", ".join(["'%s'" % x for x in ids])
				print(cmd)
				data = db.execute(cmd).fetchall()
				fieldnames = [x["name"] for x in  db.execute("PRAGMA table_info(full_results)").fetchall()]
				csv_text = ",".join(fieldnames) + "\n"
				for row in data:
					csv_text = csv_text + ",".join(['"%s"' % row[c] if (row[c]!=None and row[c]!="") else '"-"' for c in fieldnames]) + "\n"
				print(csv_text)
				return Response(csv_text,mimetype="text/csv",headers={"Content-disposition": "attachment; filename=result.csv"})
			elif request.form["button"]=="delete":
				ids = list(json.loads(request.form["ids"]).keys())
				cmd = "DELETE FROM results WHERE id in ( %s )" % ", ".join(["'%s'" % x for x in ids])
				db.execute(cmd)
				db.commit()
	return render_template('results/result_table.html', user=user)
