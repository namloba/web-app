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

from .edgex_interface import Rule




@blueprint.route('/index')
@login_required
def index():

    return render_template('home/index.html', segment='index')

# API endpoint để lấy giá trị cảm biến và trạng thái relay mới nhất
@blueprint.route('/api/<farm_name>/reading')
def get_reading(farm_name):
    resource = request.args.get('resource')
    if not farm_name or not resource:
        return jsonify({"error": "Missing farm_name or resource"}), 400

    try:
        readings = edgex.get_readings(farm_name, resource, limit=1)
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


@blueprint.route("/api/<farm_name>/statistics/<sensor_type>")
def get_sensor_data(farm_name, sensor_type):
    time_range = request.args.get("timeRange", "day")
    selected_date = request.args.get("date", datetime.date.today().isoformat())

    sensor_map = {
        "humidity": "DoAm",
        "temperature": "NhietDo",
        "light": "AnhSang"
    }
    resource = sensor_map.get(sensor_type, "NhietDo")

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

    readings = edgex.get_readings(device_name=farm_name, resource_name=resource, start_ms=start_ms, end_ms=end_ms, limit=limit)
    logging.info(f"Statistics readings for {resource}: {readings}")

    data = []
    for r in readings:
        ts = r.get("origin") or r.get("created")
        try:
            dt = datetime.datetime.fromtimestamp(int(ts/1_000_000_000))
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
    

# Lay danh sach tat ca rule (de render tren giao dien) va xoa toan bo rule (it dung)
@blueprint.route('/api/<farm_name>/rules/all', methods=['GET', 'DELETE'])
def api_get_or_delete_all_rules(farm_name):
    if request.method not in ['GET', 'DELETE']:
        return jsonify({"error": "Method not allowed"}), 405
    if request.method == 'GET':
        try:
            rule_manager = Rule(device_name=farm_name)
            rules = rule_manager.get_rules()
            return jsonify({"success": True, "rules": rules})
        except Exception as e:
            return jsonify({"error": f"Lỗi khi lấy danh sách rule: {str(e)}"}), 500
    else:  # DELETE method
        try:
            rule_manager = Rule(device_name=farm_name)
            result = rule_manager.delete_all_rules()
            if result.get("success"):
                return jsonify({"success": True, "message": "All rules deleted successfully"})
            else:
                return jsonify({"error": f"Lỗi khi xóa tất cả rule: {result.get('error', 'Unknown error')}"}), 500
        except Exception as e:
            return jsonify({"error": f"Lỗi khi xóa tất cả rule: {str(e)}"}), 500


@blueprint.route('/api/<farm_name>/rule', methods=['POST', 'DELETE'])
def api_add_or_delete_rule(farm_name):
    if request.method == 'DELETE':
        rule_id = request.args.get('id')
        if not rule_id:
            return jsonify({"error": "Missing rule ID"}), 400
        try:
            rule_manager = Rule(device_name=farm_name)
            result = rule_manager.delete_rule(int(rule_id))
            if result.get("success"):
                return jsonify({"success": True, "message": "Rule deleted successfully"})
            else:
                return jsonify({"error": f"Lỗi khi xóa rule: {result.get('error', 'Unknown error')}"}), 500
        except Exception as e:
            return jsonify({"error": f"Lỗi khi xóa rule: {str(e)}"}), 500
    elif request.method == 'POST':
        try:
            rule_json = request.get_json()
            if not rule_json:
                return jsonify({"error": "Missing rule data"}), 400
            
            num_fields = [
                "temp_min", "temp_max", "hum_min", "hum_max", "light_min", "light_max",
                "repeat_days", "start_in_minutes", "end_in_minutes", "relay_index", "logic", "id"
            ]
            for f in num_fields:
                if f in rule_json:
                    try:
                        rule_json[f] = int(rule_json[f])
                    except Exception:
                        rule_json[f] = 0
            
            rule_manager = Rule(device_name=farm_name)
            # Check if rule_manager has any rules defined (assuming Rule has a method or attribute for this)
            # If not, return a message
            if hasattr(rule_manager, "rules") and not rule_manager.rules:
                return jsonify({"error": f"Không có rule nào được định nghĩa cho thiết bị '{farm_name}'."}), 400
            result = rule_manager.add_rule(rule_json)
            if result.get("success"):
                return jsonify({"success": True, "message": "Rule added successfully"})
            else:
                return jsonify({"error": f"Lỗi khi thêm rule: {result.get('error', 'Unknown error')}"}), 500
        except Exception as e:
            return jsonify({"error": f"Lỗi khi thêm rule: {str(e)}"}), 500
            if hasattr(rule_manager, "rules") and not rule_manager.rules:
                return jsonify({"error": "Không có rule nào được định nghĩa cho thiết bị 'Tu-1'."}), 400
            result = rule_manager.add_rule(rule_json)
            if result.get("success"):
                return jsonify({"success": True, "message": "Rule added successfully"})
            else:
                # Improved error message
                return jsonify({"error": f"Lỗi khi thêm rule: {result.get('error', 'Unknown error')}"}), 500
        except Exception as e:
            # Improved error message
            return jsonify({"error": f"Lỗi khi thêm rule: {str(e)}"}), 500



