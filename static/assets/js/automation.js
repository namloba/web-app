// Thêm dòng mới vào bảng quy tắc
function addCondition() {
  const table = document.getElementById("ruleTable").getElementsByTagName('tbody')[0];
  const newRow = table.insertRow();

  newRow.innerHTML = `
    <td><input type="text" placeholder="Tên luật"></td>
    <td>
      <select>
        <option value="Nhiệt độ">Nhiệt độ</option>
        <option value="Độ ẩm đất">Độ ẩm đất</option>
        <option value="Ánh sáng">Ánh sáng</option>
        <option value="CO2">CO2</option>
        <option value="pH">pH</option>
      </select>
    </td>
    <td><input type="text" placeholder="Ngưỡng"></td>
    <td><input type="text" placeholder="Hành động"></td>
    <td><label class="switch"><input type="checkbox"><span class="slider"></span></label></td>
    
    <td><button class="delete-btn" onclick="deleteRow(this)">X</button></td>
  `;
}

// Xoá một dòng trong bảng
function deleteRow(button) {
  const row = button.parentNode.parentNode;
  row.parentNode.removeChild(row);
}

// Lưu dữ liệu từ bảng (hiện tại chỉ log ra console)
function saveRules() {
  const rows = document.querySelectorAll("#ruleTable tbody tr");
  const rules = [];

  rows.forEach(row => {
    const inputs = row.querySelectorAll("input[type='text']");
    const select = row.querySelector("select");
    const checkbox = row.querySelector("input[type='checkbox']");

    rules.push({
      ten_luat: inputs[0].value,
      cam_bien: select.value,
      nguong: inputs[1].value,
      hanh_dong: inputs[2].value,
      trang_thai: checkbox.checked
    });
  });

  console.log("Quy tắc đã lưu:", JSON.stringify(rules, null, 2));
  alert("Quy tắc đã được lưu vào console!");
}

