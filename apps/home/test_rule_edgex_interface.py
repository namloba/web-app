import edgex_interface as edgex
import time
import json


def test_get_devices():
    print("🔍 Danh sách thiết bị:")
    devices = edgex.get_all_devices()
    for d in devices:
        print(f" - {d['name']}")
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

# ================================================================
# Rule tests
# =================================================================
def test_create_rule1():
    tu = edgex.Rule('Tu-1')

    rule = {
        "id": 1,
        "repeat_days": 1,
        "start_in_minutes": 1 * 60 + 0,
        "end_in_minutes": 23 * 60 + 50,
        "start_date": "2025-06-01",
        "relay_index": 1,
        "relay_value": True,
        "reverse_on_false": True,
        "logic": 7,  # NONE
        "temp_min": 25,
        "temp_max": 35,
        "hum_min": 30,
        "hum_max": 80,
        "light_min": 20,
        "light_max": 1000
    }
    result = tu.add_rule(rule_json=rule)
    print(result)

def test_create_rule2():
    tu = edgex.Rule('Tu-1')
    
    rule = {
        "id": 30,
        "repeat_days": 1,
        "start_in_minutes": 8 * 60 + 0,
        "end_in_minutes": 20 * 60 + 0,
        "start_date": "2025-06-01",
        "relay_index": 1,
        "relay_value": True,
        "reverse_on_false": True,
        "logic": 0,  # NONE
        "temp_min": 25,
        "temp_max": 35,
        "hum_min": 30,
        "hum_max": 70,
        "light_min": 100,
        "light_max": 1000
    }
    result = tu.add_rule(rule_json=rule)
    print(result)


if __name__ == "__main__":
    test_create_rule1()
    test_create_rule2()

    # Quy trình sử dụng rule
    # 1. Tạo 1 đối tượng mới, ví dụ "tu" bằng cách gọi tu = edgex.Rule('tên của device'),
    tu = edgex.Rule('Tu-1')

    # 2. Tạo dữ liệu nếu cần (ví dụ nội dung rule)
    rule = {
        "id": 30,
        "repeat_days": 1,
        "start_in_minutes": 8 * 60 + 0,
        "end_in_minutes": 20 * 60 + 0,
        "start_date": "2025-06-01",
        "relay_index": 1,
        "relay_value": True,
        "reverse_on_false": True,
        "logic": 0,  # NONE
        "temp_min": 25,
        "temp_max": 35,
        "hum_min": 30,
        "hum_max": 70,
        "light_min": 100,
        "light_max": 1000
    }

    # 3. Gọi hàm tương ứng để thao tác với rule
    result = tu.add_rule(rule_json=rule)

    # 4. Kết quả trả về sẽ là một dict, dạng như sau: {"success": False, "error": str(e)}
    # Do do đó, bạn có thể kiểm tra kết quả bằng cách:
    if result.get("success", False):
        print("Thành công")
    else:
        print("Thất bại. Lý do:", result.get("error"))
        
    # Danh sách các hàm có thể sử dụng:
    # tu.add_rule(rule_json=rule)
    # tu.delete_rule(1)
    # tu.delete_all_rules()
    # tu.get_rules()
