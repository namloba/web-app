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
import logging



@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')

# API endpoint để lấy giá trị cảm biến và trạng thái relay mới nhất
@blueprint.route('/api/reading')
def get_reading():
    device = request.args.get('device')
    resource = request.args.get('resource')
    
    if not device or not resource:
        return jsonify({"error": "Missing device or resource"}), 400
        
    try:
        readings = edgex.get_readings(device, resource, limit=1)
        logging.info(f"Sensor readings: {readings}")
        if readings and len(readings) > 0:
            return jsonify({"value": readings[0].get("value")})
        return jsonify({"value": None})
    except Exception as e:
        logging.error(f"Error in get_reading: {e}")
        return jsonify({"error": str(e)}), 500

# API endpoint để điều khiển thiết bị
@blueprint.route('/api/device/<device>/control/<command>', methods=['POST'])
def control_device(device, command):
    try:
        state = request.json.get('state')
        if state not in ['true', 'false']:
            return jsonify({"error": "Invalid state value"}), 400
            
        # Gửi lệnh điều khiển
        result = edgex.send_command(
            device_name=device,
            command_name=command,
            method="PUT",
            body={command: state}
        )

        # Đọc lại trạng thái sau khi điều khiển để xác nhận
        verify = edgex.send_command(
            device_name=device,
            command_name=command,
            method="GET"
        )
        
        # Kiểm tra xem trạng thái đã được cập nhật chưa
        actual_state = str(verify.get(command, "false")).lower()
        success = actual_state == state
        
        return jsonify({
            "success": success,
            "state": actual_state,
            "result": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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
    
    

# API Endpoints for EdgeX interactions - Real data


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

    # Tính toán khoảng thời gian
    dt = datetime.datetime.fromisoformat(selected_date)
    if time_range == "day":
        start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        limit = 24
    elif time_range == "week":
        start = dt - datetime.timedelta(days=dt.weekday())
        end = start + datetime.timedelta(days=6)
        limit = 7
    elif time_range == "month":
        start = dt.replace(day=1)
        next_month = (start + datetime.timedelta(days=32)).replace(day=1)
        end = next_month - datetime.timedelta(seconds=1)
        limit = 30
    else:
        start = dt
        end = dt
        limit = 24

    start_ms = int(start.timestamp() * 1000)
    end_ms = int(end.timestamp() * 1000)

    readings = edgex.get_readings(device_name="Tu-1", resource_name=resource, start_ms=start_ms, end_ms=end_ms, limit=limit)
    logging.info(f"Statistics readings for {resource}: {readings}")

    data = []
    for r in readings:
        ts = r.get("origin") or r.get("created")
        try:
            dt = datetime.datetime.fromtimestamp(int(ts)/1000)
            if time_range == "day":
                label = dt.strftime("%H:%M")
            else:
                label = dt.strftime("%d/%m")
        except:
            label = "unknown"
        data.append({
            "time": label,
            "value": float(r.get("value", 0))
        })

    data = data[::-1]
    return jsonify(data)