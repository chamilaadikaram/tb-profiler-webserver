from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for
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
bp = Blueprint('upload', __name__)


@bp.route('/upload',methods=('GET', 'POST'))
def upload():
	if request.method == 'POST':
		db = get_db()
		uniq_id = str(uuid.uuid4())
		filename1 = secure_filename(request.files['file1'].filename)
		filename2 = secure_filename(request.files['file2'].filename)
		if filename1=="":
			error = "No file found for read 1, please try again!"
		if error==None:
			request.files['file1'].save(os.path.join(app.config["UPLOAD_FOLDER"], filename1))
			if filename2!="": request.files['file2'].save(os.path.join(app.config["UPLOAD_FOLDER"], filename2))
			server_fname1 = "/tmp/%s" % filename1
			server_fname2 = "/tmp/%s" % filename2 if filename2!="" else None
			sample_name = uniq_id if request.form["sample_name"]=="" else request.form["sample_name"]
			print(sample_name)
			db.execute("INSERT INTO results (id,sample_name,result) VALUES (?,?,?)",(uniq_id,sample_name,"{}"))
			db.commit()
			tbprofiler.delay(fq1=server_fname1,fq2=server_fname2,uniq_id=uniq_id,sample_name=sample_name,db=app.config["DATABASE"],storage_dir=app.config["UPLOAD_FOLDER"])
			return redirect(url_for('results.run_result', sample_id=uniq_id))
		flash(error)
	return render_template('upload/upload.html')
