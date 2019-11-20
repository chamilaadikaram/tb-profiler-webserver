from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import json
#from aseantb.auth import login_required
from tbprofiler_web.db import get_db

bp = Blueprint('home', __name__)


@bp.route('/',methods=('GET', 'POST'))
def index():
	db = get_db()
	if request.method == 'POST':
		return redirect(url_for('results.run_result', sample_id=request.form["sample_id"]))
	return render_template('home/index.html')
