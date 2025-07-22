import edgex_interface as edgex
import time
import json

def test_get_devices():
    print("🔍 Danh sách thiết bị:")
    devices = edgex.get_all_devices()
    for d in devices:
        print(f" - {d['name']}")
    print()

def test_create_stream():
    print("📡 Tạo stream 'Tu_1'")
    result = edgex.create_stream("Tu_1")
    print(result)
    print()

def test_create_rule():
    print("⚙️ Tạo rule 'bat_relay1_theo_nhietdo_doam'")
    sql = """
        SELECT NhietDo FROM Tu_1
        WHERE NhietDo >= 20 AND NhietDo <= 40
    """
    actions = [
        {
            "rest": {
                "bodyType": "json",
                "dataTemplate": "{\"Relay1\":\"true\"}",
                "method": "PUT",
                "url": "http://edgex-core-command:59882/api/v3/device/name/Tu-1/Relay1"
            }
        },
        {
            "mqtt": {
                "server": "tcp://broker.emqx.io:1883",
                "topic": "hou/edge-gatewa/noti",
                "dataTemplate": "\"rule:bat_relay1_theo_nhietdo_doam da kich hoat\""
            }
        }
    ]
    result = edgex.create_rule("bat_relay1_theo_nhietdo_doam", sql_query=sql, actions=actions)
    print(result)
    print()

def test_start_stop_rule():
    print("▶️ Start rule")
    print(edgex.start_rule("bat_relay1_theo_nhietdo_doam"))
    time.sleep(3)
    print("⏹ Stop rule")
    print(edgex.stop_rule("bat_relay1_theo_nhietdo_doam"))
    print()

def test_list_rules():
    print("📋 Danh sách rule hiện có:")
    rules = edgex.list_rules()
    for rule in rules:
        print(f" - {rule['id']} ({'running' if rule['status'] else 'stopped'})")
    print()

def test_readings(device_name: str, resource_name: str):
    print(f"📊 Đọc dữ liệu {resource_name} từ thiết bị {device_name} trong 5 phút qua")
    now = edgex.now_ms()
    before = now - 5 * 60 * 1000  # 5 phút trước
    readings = edgex.get_readings(device_name, resource_name, start_ms=before, end_ms=now, limit=5)

    for r in readings:
        try:
            origin = int(r.get('origin', 0))
            if origin <= 0:
                ts = "Unknown time"
            else:
                # Convert from nanoseconds to seconds
                ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(origin / 1_000_000_000))
            print(f"{ts} | {r['value']}")
        except Exception as e:
            print(f"[!] Lỗi khi xử lý timestamp: {e} - raw origin: {r.get('origin')}")
    print()


def test_command():
    print("🚨 Gửi lệnh bật relay qua command")
    result = edgex.send_command("Tu-1", "Relay1", method="POST", body={"Relay1": "true"})
    print(json.dumps(result, indent=2))
    print()


def test_create_threshold_rule():
    result = edgex.create_threshold_rule(
    rule_id="bat_relay1_anhsang_trongkhoang",
    stream_name="Tu_1",
    device_name="Tu-1",
    resource_name="AnhSang",
    lower=200,
    upper=400,
    relay_command="Relay1",
    relay_state="true")

    print(result)

def test_create_out_of_range_rule():
    result = edgex.create_out_of_range_rule(
    rule_id="bat_relay1_anhsang_trongkhoang_out_of_range",
    stream_name="Tu_1",
    device_name="Tu-1",
    resource_name="AnhSang",
    lower=200,
    upper=400,
    relay_command="Relay1",
    relay_state="false")

    print(result)


if __name__ == "__main__":
    test_get_devices()
    test_readings(device_name="Tu-1", resource_name="NhietDo")
    test_readings(device_name="Tu-1", resource_name="DoAm")
    test_readings(device_name="Tu-1", resource_name="AnhSang")
    # test_command()

    # edgex.delete_rule("bat_relay1_nhietdo_trongkhoang")
    # edgex.delete_rule("bat_relay1_nhietdo_trongkhoang_out_of_range")

    # test_create_threshold_rule()
    # test_create_out_of_range_rule()
    # test_create_stream()
    # test_create_rule()
    # test_start_stop_rule()
    # test_list_rules()
