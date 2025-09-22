from dotenv import load_dotenv
import os
import requests
import time
from datetime import datetime, timedelta, date
from bitstring import BitArray
import json


# Load environment variables from .env file
load_dotenv()

# ==== Base URLs ====
CORE_METADATA_URL = os.getenv("CORE_METADATA_URL")
CORE_COMMAND_URL  = os.getenv("CORE_COMMAND_URL")
CORE_DATA_URL     = os.getenv("CORE_DATA_URL")
RULE_ENGINE_URL   = os.getenv("RULE_ENGINE_URL")


# ==== DEVICE & COMMAND ====

def get_all_devices():
    try:
        url = f"{CORE_METADATA_URL}/api/v3/device/all"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("devices", [])
    except Exception as e:
        print("Error fetching devices:", e)
        return []

def get_device_by_name(name):
    try:
        url = f"{CORE_METADATA_URL}/api/v3/device/name/{name}"
        print(f"Fetching device: {url}")
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("device", {})
    except Exception as e:
        print("Error fetching device:", e)
        return {}

def update_device(device_info):
    """
    Partially update a device in EdgeX core-metadata.
    device_info: dict chứa thông tin cần update, ví dụ:
        {
            "name": "MyDevice",
            "adminState": "LOCKED"
        }
    """
    try:
        url = f"{CORE_METADATA_URL}/api/v3/device"
        body = {"apiVersion": "v3", 'device': device_info}
        response = requests.patch(url, json=[body])  # API yêu cầu list []
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Error updating device:", e)
        return {}

def send_command(device_name, command_name, method="PUT", body=None):
    """
    Gửi lệnh đến thiết bị qua core-command (GET hoặc PUT)
    """
    try:
        url = f"{CORE_COMMAND_URL}/api/v3/device/name/{device_name}/{command_name}"
        print(f"Fetching device: {url}")
        if method.upper() == "PUT":
            response = requests.put(url, json=body or {})
        else:
            response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Error sending command:", e)
        return {}


# ==== CORE-DATA (Reading History) ====

def get_readings(device_name, resource_name, start_ms=None, end_ms=None, limit=100):
    """
    Truy vấn readings theo thiết bị + resource trong khoảng thời gian
    """
    try:
        url = f"{CORE_DATA_URL}/api/v3/reading/device/name/{device_name}/resourceName/{resource_name}"
        params = {"limit": limit}
        if start_ms: params["start"] = start_ms
        if end_ms: params["end"] = end_ms

        # print(f"Fetching device: {url}")

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json().get("readings", [])
    except Exception as e:
        print("Error fetching readings:", e)
        return []

# ==== (Optional) Epoch helper ====

def now_ms():
    """Trả về thời gian hiện tại dạng epoch milliseconds"""
    return int(time.time() * 1000)

def calculate_days_since_2025(date_string):
    """
    Tính số ngày từ một ngày cụ thể đến đầu năm 2025.

    Args:
        date_string (str): Chuỗi ngày ở định dạng 'yyyy-mm-dd'.
    
    Returns:
        int: Số ngày từ ngày 1/1/2025 đến ngày được truyền vào.
    """
    try:
        # Chuyển đổi chuỗi ngày thành đối tượng date
        input_date = date.fromisoformat(date_string)
    except ValueError:
        print("Lỗi: Định dạng ngày không hợp lệ. Vui lòng sử dụng 'yyyy-mm-dd'.")
        return None

    # Định nghĩa mốc thời gian (epoch) là ngày 1 tháng 1 năm 2025
    epoch_date = date(2025, 1, 1)

    # Tính toán khoảng thời gian giữa hai ngày
    delta = input_date - epoch_date

    # Trả về số ngày
    return delta.days


def convert_days_to_date(days_since_2025):
    """
    Chuyển đổi số ngày từ đầu năm 2025 về định dạng ngày chuẩn 'yyyy-mm-dd'.
    
    Args:
        days_since_2025 (int): Số ngày tính từ ngày 01/01/2025.
        
    Returns:
        str: Chuỗi ngày ở định dạng 'yyyy-mm-dd'.
    """
    # Định nghĩa mốc thời gian (epoch) là ngày 1 tháng 1 năm 2025
    epoch_date = date(2025, 1, 1)

    # Thêm số ngày vào mốc thời gian
    result_date = epoch_date + timedelta(days=days_since_2025)

    # Trả về chuỗi ngày đã được định dạng
    return result_date.isoformat()

# ==== Quản lý danh sách rule cục bộ ====
class Rule:
    TEMP_MIN = -20.0
    TEMP_MAX = 80.0
    HUM_MIN = 0
    HUM_MAX = 100
    LIGHT_MIN = 0
    LIGHT_MAX = 65535
    MAX_RULES = 32  # Giới hạn số lượng rule

    def __init__(self, device_name):
        """
        Khởi tạo class Rule với tên thiết bị và danh sách rule.
        """
        self.device_name = device_name
        self.rule_list = self._get_list()  # Lấy danh sách rule từ thiết bị khi khởi tạo

    def _encode(self, rule):
        """
        Mã hóa một dictionary rule thành một gói tin bytes 16-byte.

        Args:
            rule: Một dictionary chứa các trường của rule.

        Returns:
            bytes: Gói tin 16-byte.
        """
        s = BitArray()

        temp_min_val = max(self.TEMP_MIN, min(self.TEMP_MAX, rule["temp_min"]))
        temp_max_val = max(self.TEMP_MIN, min(self.TEMP_MAX, rule["temp_max"]))
        encoded_temp_min = int(temp_min_val * 10) + 200
        encoded_temp_max = int(temp_max_val * 10) + 200

        hum_min_val = max(self.HUM_MIN, min(self.HUM_MAX, rule["hum_min"]))
        hum_max_val = max(self.HUM_MIN, min(self.HUM_MAX, rule["hum_max"]))

        light_min_val = max(self.LIGHT_MIN, min(self.LIGHT_MAX, rule["light_min"]))
        light_max_val = max(self.LIGHT_MIN, min(self.LIGHT_MAX, rule["light_max"]))

        start_date_since_2025 = calculate_days_since_2025(rule["start_date"])
        if start_date_since_2025 is None or start_date_since_2025 < 0 or start_date_since_2025 > 65535:
            raise ValueError("Lỗi mã hóa: Ngày bắt đầu không hợp lệ hoặc ngoài phạm vi.")
        if rule['id'] < 0 or rule['id'] >= 32:
            raise ValueError("Lỗi mã hóa: ID rule phải trong khoảng 0-31.")
        if rule['repeat_days'] < 0 or rule['repeat_days'] >= 32:
            raise ValueError("Lỗi mã hóa: repeat_days phải trong khoảng 0-31.")
        if rule['start_in_minutes'] < 0 or rule['start_in_minutes'] >= 1440:
            raise ValueError("Lỗi mã hóa: start_in_minutes phải trong khoảng 0-1439.")
        if rule['end_in_minutes'] < 0 or rule['end_in_minutes'] >= 1440:
            raise ValueError("Lỗi mã hóa: end_in_minutes phải trong khoảng 0-1439.")
        if rule['relay_index'] < 0 or rule['relay_index'] >= 8:
            raise ValueError("Lỗi mã hóa: relay_index phải trong khoảng 0-7.")
        if rule['logic'] < 0 or rule['logic'] >= 8:
            raise ValueError("Lỗi mã hóa: logic phải trong khoảng 0-7.")
        if encoded_temp_min < 0 or encoded_temp_min >= 1024:
            raise ValueError("Lỗi mã hóa: temp_min ngoài phạm vi.")
        if encoded_temp_max < 0 or encoded_temp_max >= 1024:
            raise ValueError("Lỗi mã hóa: temp_max ngoài phạm vi.")
        if hum_min_val < 0 or hum_min_val >= 1024:
            raise ValueError("Lỗi mã hóa: hum_min ngoài phạm vi.")
        if hum_max_val < 0 or hum_max_val >= 1024:
            raise ValueError("Lỗi mã hóa: hum_max ngoài phạm vi.")
        if light_min_val < 0 or light_min_val >= 65536:
            raise ValueError("Lỗi mã hóa: light_min ngoài phạm vi.")
        if light_max_val < 0 or light_max_val >= 65536:
            raise ValueError("Lỗi mã hóa: light_max ngoài phạm vi.")
        

        s.append('uint:5={}'.format(rule['id']))
        s.append('uint:5={}'.format(rule['repeat_days']))
        s.append('uint:11={}'.format(rule['start_in_minutes']))
        s.append('uint:11={}'.format(rule['end_in_minutes']))
        s.append('uint:16={}'.format(start_date_since_2025))
        s.append('uint:3={}'.format(rule['relay_index']))
        s.append('bool:1={}'.format(rule['relay_value']))
        s.append('bool:1={}'.format(rule['reverse_on_false']))
        s.append('uint:3={}'.format(rule['logic']))
        s.append('uint:10={}'.format(encoded_temp_min))
        s.append('uint:10={}'.format(encoded_temp_max))
        s.append('uint:10={}'.format(hum_min_val))
        s.append('uint:10={}'.format(hum_max_val))
        s.append('uint:16={}'.format(light_min_val))
        s.append('uint:16={}'.format(light_max_val))

        if s.length != 128:
            raise ValueError("Lỗi mã hóa: Kích thước bit không đúng.")

        return s.bytes

    def _decode(self, payload_bytes):
        """
        Giải mã một gói tin rule 16-byte thành một dictionary.

        Args:
            payload_bytes (bytes): Gói tin 16-byte.

        Returns:
            dict: Rule đã giải mã.
        """
        if len(payload_bytes) != 16:
            raise ValueError("Payload phải có đúng 16 byte.")

        s = ConstBitStream(payload_bytes)

        rule = {
            "id": s.read('uint:5'),
            "repeat_days": s.read('uint:5'),
            "start_in_minutes": s.read('uint:11'),
            "end_in_minutes": s.read('uint:11'),
            "start_date": s.read('uint:16'),
            "relay_index": s.read('uint:3'),
            "relay_value": s.read('bool:1'),
            "reverse_on_false": s.read('bool:1'),
            "logic": s.read('uint:3'),
            "temp_min": s.read('uint:10'),
            "temp_max": s.read('uint:10'),
            "hum_min": s.read('uint:10'),
            "hum_max": s.read('uint:10'),
            "light_min": s.read('uint:16'),
            "light_max": s.read('uint:16')
        }

        rule["temp_min"] = (rule["temp_min"] - 200) / 10.0
        rule["temp_max"] = (rule["temp_max"] - 200) / 10.0
        rule["hum_min"] = rule["hum_min"] / 10.0
        rule["hum_max"] = rule["hum_max"] / 10.0

        rule["start_date"] = convert_days_to_date(rule["start_date"])

        return rule

    def _get_list(self):
        """
        Lấy danh sách các rule từ trường 'protocols' của thiết bị.

        Returns:
            list: Danh sách các rule (nếu có), hoặc một danh sách rỗng nếu không tìm thấy.
        """
        try:
            device_info = get_device_by_name(self.device_name)
            if not device_info:
                print(f"Không tìm thấy thiết bị với tên '{self.device_name}'.")
                return []

            print(f"Device info: {device_info}")
            protocols = device_info.get("protocols", {})
            rules_root = protocols.get("Rules", {})
            rules = rules_root.get("rules", [])

            if not rules:
                print(f"Không có rule nào được định nghĩa cho thiết bị '{self.device_name}'.")
                return []

            return rules

        except Exception as e:
            print(f"Lỗi khi lấy danh sách rule cho thiết bị '{self.device_name}': {e}")
            return []

    def _save(self):
        """
        Cập nhật danh sách rules vào trường 'rules' trong protocols của thiết bị.

        Returns:
            dict: Thông tin phản hồi từ meta service hoặc thông báo lỗi.
        """
        try:
            device_info = get_device_by_name(self.device_name)
            if not device_info:
                print(f"Không tìm thấy thiết bị với tên '{self.device_name}'.")
                return {"success": False, "error": "Device not found"}

            protocols = device_info.get("protocols", {})
            protocols["Rules"] = {"rules": self.rule_list}  # Đảm bảo chuyển đổi đúng định dạng
            device_info["protocols"] = protocols

            new_device_info = {
                "name": self.device_name,
                "protocols": device_info.get("protocols", {})
            }

            if update_device(new_device_info) == {}:
                print(f"Lỗi khi cập nhật thiết bị '{self.device_name}'.")
                return {"success": False, "error": "Failed to update device"}

            print(f"Đã cập nhật rules cho thiết bị '{self.device_name}'.")
            return {"success": True, "device": device_info}

        except Exception as e:
            print(f"Lỗi khi lưu danh sách rules cho thiết bị '{self.device_name}': {e}")
            return {"success": False, "error": str(e)}

    def _add_or_update(self, new_rule):
        """
        Thêm hoặc cập nhật một rule trong danh sách.

        Args:
            new_rule (dict): Rule mới cần thêm hoặc cập nhật.

        Returns:
            None
        """
        if "id" not in new_rule:
            print("Lỗi: Rule không có ID.")
            return

        rule_id = new_rule["id"]
        is_updated = False

        for i, rule in enumerate(self.rule_list):
            if rule.get("id") == rule_id:
                self.rule_list[i] = new_rule
                is_updated = True
                print(f"Rule có ID {rule_id} đã được cập nhật.")
                break

        if not is_updated:
            self.rule_list.append(new_rule)
            print(f"Đã thêm rule mới với ID {rule_id}.")

    def _delete_by_id(self, rule_id):
        """
        Xóa một rule khỏi danh sách dựa trên ID.

        Args:
            rule_id (int): ID của rule cần xóa.

        Returns:
            None
        """
        initial_len = len(self.rule_list)
        self.rule_list = [rule for rule in self.rule_list if rule.get("id") != rule_id]

        if len(self.rule_list) < initial_len:
            print(f"Đã xóa rule có ID {rule_id}.")
        else:
            print(f"Không tìm thấy rule có ID {rule_id}.")

    def _clear_all(self):
        """
        Xóa tất cả các rule khỏi danh sách.

        Returns:
            None
        """
        self.rule_list = []
        print("Đã xóa tất cả các rule.")
    
    def get_rules(self):
        """
        Trả về danh sách các rule hiện tại.

        Returns:
            list: Danh sách các rule.
        """
        self._get_list()
        return self.rule_list

    def add_rule(self, rule_json):
        """
        Thêm một rule mới:
        1. Encode rule thành payload.
        2. Gửi lệnh tới core-command với resource name = "SetRule".
        3. Nếu thành công, gọi hàm _add_or_update để cập nhật rule vào danh sách.
        4. Lưu danh sách rule mới vào metadata.

        Args:
            rule_json (dict): Rule mới cần thêm.

        Returns:
            dict: Kết quả của quá trình thêm rule.
        """
        try:
            # 1. Encode rule thành payload
            payload = self._encode(rule_json)
            print(payload)

            # 2. Gửi lệnh tới core-command
            resource_name = "SetRule"
            body = {resource_name: ",".join(str(b) for b in payload)}  # Chuyển payload (bytes) thành mảng byte
            print(body)
            response = send_command(self.device_name, resource_name, method="PUT", body=body)

            # Kiểm tra HTTP status code
            if response.get("statusCode") != 200:
                print(f"Lỗi khi gửi lệnh tới core-command: {response}")
                return {"success": False, "error": "Failed to send command to core-command"}

            # 3. Gọi hàm _add_or_update để cập nhật rule vào danh sách
            self._add_or_update(rule_json)

            # 4. Lưu danh sách rule mới vào metadata
            save_result = self._save()
            if not save_result["success"]:
                print(f"Lỗi khi lưu danh sách rule vào metadata: {save_result}")
                return {"success": False, "error": "Failed to save rules to metadata"}

            print(f"Rule mới đã được thêm và lưu thành công: {rule_json}")
            return {"success": True}

        except Exception as e:
            print(f"Lỗi khi thêm rule: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_rule(self, rule_id):
        """
        Xóa một rule:
        1. Gửi lệnh xóa rule tới Core Command.
        2. Gọi hàm _delete_by_id để xóa rule khỏi danh sách.
        3. Lưu danh sách rule mới vào metadata.
        Args:
            rule_id (int): ID của rule cần xóa.
        Returns:
            dict: Kết quả của quá trình xóa rule.
        """
        try:
            # 1. Gửi lệnh tới core-command
            resource_name = "DeleteRule"
            body = {resource_name: int(rule_id)}  # Chuyển payload (bytes) thành mảng byte
            response = send_command(self.device_name, resource_name, method="PUT", body=body)

            # Kiểm tra HTTP status code
            if response.get("statusCode") != 200:
                print(f"Lỗi khi gửi lệnh tới core-command: {response}")
                return {"success": False, "error": "Failed to send command to core-command"}

            # 2. Gọi hàm _delete_by_id để xóa rule khỏi danh sách
            self._delete_by_id(rule_id)

            # 3. Lưu danh sách rule mới vào metadata
            save_result = self._save()
            if not save_result["success"]:
                print(f"Lỗi khi lưu danh sách rule vào metadata: {save_result}")
                return {"success": False, "error": "Failed to save rules to metadata"}

            print(f"Rule với ID {rule_id} đã được xóa và lưu thành công.")
            return {"success": True}

        except Exception as e:
            print(f"Lỗi khi thêm rule: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_all_rules(self):
        """
        Xóa tất cả các rule:
        1. Gửi lệnh xóa tất cả rule tới Core Command.
        2. Gọi hàm _clear_all để xóa toàn bộ rule khỏi danh sách.
        3. Lưu danh sách rule mới vào metadata.
        Returns:
            dict: Kết quả của quá trình xóa tất cả rule.
        """
        try:
            # 1. Gửi lệnh tới core-command
            resource_name = "DeleteAllRules"
            body = {resource_name: 1}  # Chuyển payload (bytes) thành mảng byte
            response = send_command(self.device_name, resource_name, method="PUT", body=body)

            # Kiểm tra HTTP status code
            if response.get("statusCode") != 200:
                print(f"Lỗi khi gửi lệnh tới core-command: {response}")
                return {"success": False, "error": "Failed to send command to core-command"}

            # 2. Gọi hàm _clear_all để xóa toàn bộ rule khỏi danh sách
            self._clear_all()   

            # 3. Lưu danh sách rule mới vào metadata
            save_result = self._save()
            if not save_result["success"]:
                print(f"Lỗi khi lưu danh sách rule vào metadata: {save_result}")
                return {"success": False, "error": "Failed to save rules to metadata"}

            print("Tất cả các rule đã được xóa và lưu thành công.")
            return {"success": True}

        except Exception as e:
            print(f"Lỗi khi xóa tất cả rule: {e}")
            return {"success": False, "error": str(e)}
