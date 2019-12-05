from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, Response
)
from werkzeug.exceptions import abort
import subprocess
#from aseantb.auth import login_required
from tbprofiler_web.db import get_db
from tbprofiler_web.worker import tbprofiler
import uuid
from werkzeug.utils import secure_filename
import os
from flask import current_app as app
from tbprofiler_web.utils import get_fastq_md5
import re
bp = Blueprint('upload', __name__)

def run_sample(db,uniq_id,f1,f2=None):
	filename1 = secure_filename(f1.filename)
	filename2 = secure_filename(f2.filename)
	f1.save(os.path.join(app.config["UPLOAD_FOLDER"], filename1))
	if filename2:
		f2.save(os.path.join(app.config["UPLOAD_FOLDER"], filename2))
	server_fname1 = "/tmp/%s" % filename1
	server_fname2 = "/tmp/%s" % filename2 if filename2!="" else None
	sample_name = uniq_id
	db.execute("INSERT INTO results (id,sample_name,result) VALUES (?,?,?)",(uniq_id,sample_name,"{}"))
	db.commit()
	tbprofiler.delay(fq1=server_fname1,fq2=server_fname2,uniq_id=uniq_id,sample_name=sample_name,db=app.config["DATABASE"],storage_dir=app.config["UPLOAD_FOLDER"])

@bp.route('/upload',methods=('GET', 'POST'))
def upload():
	db = get_db()
	if request.method == 'POST':
		print(request.form)
		error=None
		if "single_sample_submit" in request.form:
			uniq_id = str(uuid.uuid4())
			if request.files['file1'].filename=="":
				error = "No file found for read 1, please try again!"
			if error==None:
				run_sample(db,uniq_id,request.files['file1'],request.files['file2'])
				return redirect(url_for('results.run_result', sample_id=uniq_id))
		elif "multi_sample_submit" in request.form:
			files = {f.filename:f for f in list(request.files.lists())[0][1]}
			if len(files)%2!=0:
				error = "Odd number of files. There should be two files per sample, please check."
			if error==None:
				prefixes = set()
				for f in files.keys():
					tmp = re.search("(.+)_[12].fastq.gz",f)
					if tmp==None:
						error = "%s does not contain '_1.fastq.gz' or '_2.fastq.gz' as the file ending. Please revise your file names" % f
						break
					prefixes.add(tmp.group(1))
			if error==None:
				runs = []
				for p in prefixes:
					uniq_id = str(uuid.uuid4())
					r1 = "%s_1.fastq.gz" % p
					r2 = "%s_2.fastq.gz" % p
					if r1 not in files:
						error = "%s is present in data file but not %s. Please check." % (r2,r1)
					if r2 not in files:
						error = "%s is present in data file but not %s. Please check." % (r1,r2)
					runs.append({"ID":uniq_id,"R1":r1,"R2":r2})
			if error==None:
				csv_text = "ID,R1,R2\n" + "\n".join(["%(ID)s,%(R1)s,%(R2)s" % d for d in runs])
				for run in runs:
					run_sample(db,run["ID"],files[run["R1"]],files[run["R2"]])

				return Response(csv_text,mimetype="text/csv",headers={"Content-disposition": "attachment; filename=tb-profiler-IDs.csv"})

		flash(error)
	return render_template('upload/upload.html')
