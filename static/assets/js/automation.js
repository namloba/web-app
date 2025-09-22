const farmName = localStorage.getItem('farmName'); // Đặt lên đầu file

// state
let rules = [];

// helpers
function qAll(sel, root = document) {
    return Array.from(root.querySelectorAll(sel));
}
function q(sel, root = document) {
    return root.querySelector(sel);
}

// --- MAPPINGS ---
const MAPPINGS = {
    RELAY_INDEX: { FAN: 0, LIGHT: 1, PUMP1: 2, PUMP2: 3 },
    RELAY_VALUE: { ON: true, OFF: false },
    SENSOR: {
        temperature: { min: -20, max: 80, label: 'Nhiệt độ' },
        humidity: { min: 0, max: 100, label: 'Độ ẩm' },
        light: { min: 0, max: 65535, label: 'Ánh sáng' }
    }
};

const referenceDate = new Date('2025-01-01');
function dateToDays(dateStr) {
    if (!dateStr) return null;
    return Math.floor((new Date(dateStr).getTime() - referenceDate.getTime()) / 86400000);
}
function timeToMinutes(timeStr) {
    if (!timeStr) return 0;
    const [h, m] = timeStr.split(':').map(Number);
    return h * 60 + m;
}
function minutesToTime(minutes) {
    if (minutes === null) return '-';
    return String(Math.floor(minutes / 60)).padStart(2, '0') + ":" + String(minutes % 60).padStart(2, '0');
}

function findAvailableId() {
    const used = new Set(rules.map(r => r.id));
    for (let i = 0; i <= 31; i++) if (!used.has(i)) return i;
    return null;
}

// render rules table
function renderRules() {
    const tbody = q('#tbodyRules');
    tbody.innerHTML = '';
    rules.forEach((r, i) => {
        const condSummary = summarizeConditions(r);
        const timeSummary = `${r.start_date || '-'} | ${minutesToTime(r.start_in_minutes)}-${minutesToTime(r.end_in_minutes)} | mỗi ${r.repeat_days || 1} ngày`;
        const actionSummary = `${r.relay_value ? 'Bật' : 'Tắt'} ${Object.keys(MAPPINGS.RELAY_INDEX).find(k => MAPPINGS.RELAY_INDEX[k] === r.relay_index) || 'Thiết bị'} ${r.reverse_on_false ? '(ngược lại thì đảo trạng thái)' : ''}`;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${i + 1}</td>
            <td>${escapeHtml(condSummary)}</td>
            <td>${escapeHtml(actionSummary)}</td>
            <td>${escapeHtml(timeSummary)}</td>
            <td style="text-align:right"><button class="btn-danger" data-del="${i}">Xóa</button></td>`;
        tbody.appendChild(tr);
    });
    qAll('button[data-del]').forEach(btn => btn.onclick = async () => {
        const idx = parseInt(btn.dataset.del);
        if (confirm('Xóa luật # ' + (idx + 1) + '?')) {
            const ruleId = rules[idx].id;
            if (await deleteRule(ruleId)) { // Gọi API xóa rule trên server
                rules.splice(idx, 1);
                renderRules();
            }
        }
    });
}

function summarizeConditions(rule) {
    const p = [];
    const humLogic = (rule.logic >> 1) & 1;
    const lightLogic = (rule.logic >> 2) & 1;

    if (rule.temp_min > MAPPINGS.SENSOR.temperature.min || rule.temp_max < MAPPINGS.SENSOR.temperature.max) {
        if (rule.temp_min > MAPPINGS.SENSOR.temperature.min && rule.temp_max < MAPPINGS.SENSOR.temperature.max)
            p.push(`Nhiệt độ [${rule.temp_min} - ${rule.temp_max}]`);
        else if (rule.temp_min > MAPPINGS.SENSOR.temperature.min)
            p.push(`Nhiệt độ >= ${rule.temp_min}`);
        else p.push(`Nhiệt độ <= ${rule.temp_max}`);
    }
    if (rule.hum_min > MAPPINGS.SENSOR.humidity.min || rule.hum_max < MAPPINGS.SENSOR.humidity.max) {
        const logicText = humLogic ? 'VÀ' : 'HOẶC';
        p.push(`${logicText} Độ ẩm ${rule.hum_min}-${rule.hum_max}`);
    }
    if (rule.light_min > MAPPINGS.SENSOR.light.min || rule.light_max < MAPPINGS.SENSOR.light.max) {
        const logicText = lightLogic ? 'VÀ' : 'HOẶC';
        p.push(`${logicText} Ánh sáng ${rule.light_min}-${rule.light_max}`);
    }
    return p.join(' ');
}

function escapeHtml(s) {
    return (s ?? '').toString().replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

function openModal() {
    q('#modal').classList.add('show');
    q('#modalTitle').textContent = 'Tạo luật mới';
    q('#dateStart').value = '';
    q('#repeatDays').value = 1;
    q('#timeStart').value = '';
    q('#timeEnd').value = '';
    q('#actionDevice').value = 'PUMP1';
    q('#actionStatus').value = 'ON';
    q('#reverseOnFalse').checked = false;
    qAll('.val-min').forEach(e => e.value = '');
    qAll('.val-max').forEach(e => e.value = '');
}
function closeModal() {
    q('#modal').classList.remove('show');
}

function readRuleFromModal() {
    const newId = findAvailableId();
    if (newId === null) { alert("Tối đa 32 rule."); return null; }
    const rows = qAll('#modal .modal-box tbody tr');
    const startDateValue = q('#dateStart').value;
    const rule = {
        repeat_days: parseInt(q('#repeatDays').value || '1', 10),
        start_in_minutes: timeToMinutes(q('#timeStart').value),
        end_in_minutes: timeToMinutes(q('#timeEnd').value),
        start_date: startDateValue ? startDateValue : "", // sửa: luôn là string
        relay_index: MAPPINGS.RELAY_INDEX[q('#actionDevice').value],
        relay_value: MAPPINGS.RELAY_VALUE[q('#actionStatus').value],
        reverse_on_false: !!q('#reverseOnFalse').checked,
        logic: ((rows[1].querySelector('.logic-select').value === 'AND') << 1) | ((rows[2].querySelector('.logic-select').value === 'AND') << 2),
        temp_min: parseInt(rows[0].querySelector('.val-min').value || MAPPINGS.SENSOR.temperature.min, 10),
        temp_max: parseInt(rows[0].querySelector('.val-max').value || MAPPINGS.SENSOR.temperature.max, 10),
        hum_min: parseInt(rows[1].querySelector('.val-min').value || MAPPINGS.SENSOR.humidity.min, 10),
        hum_max: parseInt(rows[1].querySelector('.val-max').value || MAPPINGS.SENSOR.humidity.max, 10),
        light_min: parseInt(rows[2].querySelector('.val-min').value || MAPPINGS.SENSOR.light.min, 10),
        light_max: parseInt(rows[2].querySelector('.val-max').value || MAPPINGS.SENSOR.light.max, 10),
        id: newId
    };
    return rule;
}

// Hàm lưu dữ liệu, đã được sửa để trả về promise như đã giải thích
async function saveRuleToDatabase(rule) {
    try {
        const response = await fetch(`/api/${farmName}/rule`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rule)
        });

        const data = await response.json();

        if (response.ok) {
            if (data.error) {
                console.error('Lỗi từ server:', data.error);
                alert('Lỗi khi lưu rule: ' + data.error);
                return false;
            } else {
                console.log('Rule đã được lưu thành công:', data);
                alert('Rule đã được lưu vào database!');
                return true;
            }
        } else {
            console.error('Lỗi HTTP:', response.status, response.statusText);
            alert('Lỗi khi kết nối hoặc xử lý yêu cầu.');
            return false;
        }
    } catch (error) {
        console.error('Lỗi mạng hoặc xử lý:', error);
        alert('Lỗi kết nối tới server: ' + error.message);
        return false;
    }
}

async function saveRule() {
    const r = readRuleFromModal();
    if (!r) return;
    
    console.log('Rule JSON:', JSON.stringify(r, null, 2));
    const setRuleStr = ruleToSetRuleString(r);
    console.log('SetRule:', setRuleStr);

    // Vô hiệu hóa nút lưu để tránh nhấn liên tục
    const saveButton = document.querySelector('#your-save-button-id'); // Thay bằng ID nút của bạn
    if (saveButton) {
        saveButton.disabled = true;
    }
    
    // Sử dụng await để chờ kết quả từ saveRuleToDatabase
    const success = await saveRuleToDatabase(r); // Chờ cho đến khi hàm này hoàn thành
    
    // Kích hoạt lại nút
    if (saveButton) {
        saveButton.disabled = false;
    }

    if (success) {
        console.log('Rule đã được lưu vào database, thêm vào danh sách tạm thời.');
        rules.push(r);
        renderRules();
        closeModal();
    } else {
        console.log('Rule không được lưu vào database, không thêm vào danh sách tạm thời.');
    }
}

async function fetchRulesFromServer() {
    try {
        const response = await fetch(`/api/${farmName}/rules/all`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }  
        const data = await response.json();
        if (data.error) {
            console.error('Lỗi từ server:', data.error);
            alert('Lỗi khi lấy rules: ' + data.error);
            return [];
        }   
        return data.rules || [];
    } catch (error) {
        console.error('Lỗi mạng hoặc xử lý:', error);
        alert('Lỗi kết nối tới server: ' + error.message);
        return [];
    } 
}

// Khởi tạo: lấy rules từ server và render
(async () => {
    const fetchedRules = await fetchRulesFromServer();
    if (fetchedRules.length > 0) {
        rules = fetchedRules;
        renderRules();
    }
})();

async function deleteRule(ruleId) {
    try {
        const response = await fetch(`/api/${farmName}/rule?id=${ruleId}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.error) {
            console.error('Lỗi từ server:', data.error);
            alert('Lỗi khi xóa rule: ' + data.error);
            return false;
        }
        return true;
    } catch (error) {
        console.error('Lỗi mạng hoặc xử lý:', error);
        alert('Lỗi kết nối tới server: ' + error.message);
        return false;
    }
}

// Convert rule object to SetRule string format
function ruleToSetRuleString(rule) {
    // Compose the array in the order: id, relay_index, relay_value, start_in_minutes, repeat_days, logic, temp_min, temp_max, hum_min, hum_max, light_min, light_max
    // relay_value: ON=true->1, OFF=false->0
    // reverse_on_false: add as last field (1/0)
    // start_date: convert to days since referenceDate
    const arr = [
        rule.id,
        rule.relay_index,
        rule.relay_value ? 1 : 0,
        rule.start_in_minutes,
        rule.repeat_days,
        rule.logic,
        Number(rule.temp_min),
        Number(rule.temp_max),
        Number(rule.hum_min),
        Number(rule.hum_max),
        Number(rule.light_min),
        Number(rule.light_max),
        dateToDays(rule.start_date) ?? 0,
        rule.end_in_minutes,
        rule.reverse_on_false ? 1 : 0
    ];
    return arr.join(',');
}

function loadRulesFromJson(jsonRules) {
    try {
        const parsed = JSON.parse(jsonRules);
        if (Array.isArray(parsed)) { rules = parsed; renderRules(); }
    } catch (e) { console.error("Lỗi JSON:", e); }
}

q('#btnAdd').onclick = openModal;
q('#btnClose').onclick = closeModal;
q('#btnCancel').onclick = closeModal;
q('#btnSave').onclick = saveRule; // Đảm bảo nút "Lưu" gọi đúng hàm saveRule

renderRules();
