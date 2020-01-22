from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, Response
)
from werkzeug.exceptions import abort
import json
from tbprofiler_web.auth import login_required
from tbprofiler_web.db import get_db
import tbprofiler as tbp
bp = Blueprint('mutations', __name__)



@bp.route('/mutations')
def mutations():
	db = get_db()
	tmp = db.execute("SELECT * FROM mutations", (str(sample_id),) ).fetchall()
	if tmp == None:
		error = "No mutation found"
    mutations = []
    for x in tmp:
        mutations.append(dict(x))

	return render_template('mutations/mutations_home.html',mutations=mutations)
