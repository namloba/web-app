function addCondition() {
  const table = document.getElementById("ruleTable").getElementsByTagName('tbody')[0];
  const newRow = table.insertRow();

  newRow.innerHTML = `
    <td><input type="text" placeholder="ID"></td>
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
    <td><label class="switch"><input type="checkbox"><span class="slider"></span></label></td>
    <td><button class="delete-btn" onclick="deleteRow(this)">X</button></td>
  `;
}


function deleteRow(button) {
  const row = button.parentNode.parentNode;
  row.parentNode.removeChild(row);
}

function saveData() {
  const rows = document.querySelectorAll("#ruleTable tbody tr");
  const data = [];

  rows.forEach(row => {
    const inputs = row.querySelectorAll("input[type='text']");
    const select = row.querySelector("select");
    const switches = row.querySelectorAll("input[type='checkbox']");

    data.push({
      id: inputs[0].value,
      cam_bien: select.value,
      nguong: inputs[1].value,
      hanh_dong: inputs[2].value,
      trang_thai: switches[0].checked,
      tu_dong: switches[1].checked
    });
  });

  console.log("Dữ liệu lưu:", JSON.stringify(data, null, 2));
  alert("Dữ liệu đã được lưu vào console!");
}
function saveRules() {
  const rows = document.querySelectorAll("#ruleTable tbody tr");
  const rules = [];

  rows.forEach(row => {
    const inputs = row.querySelectorAll("input[type='text']");
    const select = row.querySelector("select");
    const switches = row.querySelectorAll("input[type='checkbox']");

    rules.push({
      id: inputs[0].value,
      cam_bien: select.value,
      nguong: inputs[1].value,
      hanh_dong: inputs[2].value,
      trang_thai: switches[0].checked,
      tu_dong: switches[1].checked
    });
  });

  console.log("Quy tắc đã lưu:", JSON.stringify(rules, null, 2));
  alert("Quy tắc đã được lưu vào console!");
}

