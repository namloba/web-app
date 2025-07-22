# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound
from . import edgex_interface as edgex
from flask import jsonify, request
import datetime
import random


@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')


@blueprint.route('/automation')
@login_required
def automation():
    return render_template('home/automation.html', segment='automation')

@blueprint.route('/statistics', methods=['GET'])
@login_required
def statistics():
    
    return render_template('home/statistics.html', segment='statistics')




@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
    
    

# API Endpoints for EdgeX interactions
# @blueprint.route('/api/nhietdo')
# @login_required
# def get_nhiet_do():
#     readings = edgex.get_readings(device_name="Tu-1", resource_name="NhietDo", limit=1)
#     if readings:
#         return jsonify({"value": readings[0].get("value", "--")})
#     return jsonify({"value": "--"})

@blueprint.route('/api/reading')
@login_required
def get_single_reading():
    # Giả lập dữ liệu cảm biến
    resource = request.args.get("resource", "NhietDo")
    fake_value = {
        "NhietDo": round(random.uniform(25, 35), 1),   # 25.0 - 35.0 °C
        "DoAm": round(random.uniform(50, 90), 1),      # 50 - 90 %
        "AnhSang": random.randint(100, 1000)           # 100 - 1000 lux
    }.get(resource, "--")
    
    return jsonify({"value": fake_value}) 

@blueprint.route("/api/device/<device>/control/<command>", methods=["POST"])
def control_device(device, command):
    data = request.get_json()
    state = data.get("state", "false")
    try:
        result = edgex.send_command(device, command, method="PUT", body={command: state})
        return jsonify({"success": True, "response": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@blueprint.route("/api/statistics/<sensor_type>")
def get_sensor_data(sensor_type):
    time_range = request.args.get("timeRange", "day")
    selected_date = request.args.get("date", datetime.date.today().isoformat())

    # Mapping sensor_type → EdgeX resource name
    sensor_map = {
        "humidity": "DoAm",
        "temperature": "NhietDo",
        "light": "AnhSang"
    }
    resource = sensor_map.get(sensor_type, "NhietDo")

    # Gọi EdgeX để lấy dữ liệu mới nhất
    readings = edgex.get_readings(device_name="Tu-1", resource_name=resource, limit=24)

    data = []
    for r in readings:
        ts = r.get("origin") or r.get("created")  # milliseconds
        try:
            dt = datetime.datetime.fromtimestamp(int(ts)/1000)
            label = dt.strftime("%H:%M") if time_range == "day" else dt.strftime("%d/%m")
        except:
            label = "unknown"
        data.append({
            "time": label,
            "value": float(r.get("value", 0))
        })

    data = data[::-1]  # đảo ngược thời gian mới nhất về sau cùng
    return jsonify(data)