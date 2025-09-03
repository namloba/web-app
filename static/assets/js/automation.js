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
    qAll('button[data-del]').forEach(btn => btn.onclick = () => {
        const idx = parseInt(btn.dataset.del);
        if (confirm('Xóa luật # ' + (idx + 1) + '?')) {
            rules.splice(idx, 1);
            renderRules();
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
    const rule = {
        repeat_days: parseInt(q('#repeatDays').value || '1', 10),
        start_in_minutes: timeToMinutes(q('#timeStart').value),
        end_in_minutes: timeToMinutes(q('#timeEnd').value),
        start_date: q('#dateStart').value || null,
        relay_index: MAPPINGS.RELAY_INDEX[q('#actionDevice').value],
        relay_value: MAPPINGS.RELAY_VALUE[q('#actionStatus').value],
        reverse_on_false: !!q('#reverseOnFalse').checked,
        logic: ((rows[1].querySelector('.logic-select').value === 'AND') << 1) | ((rows[2].querySelector('.logic-select').value === 'AND') << 2),
        temp_min: rows[0].querySelector('.val-min').value || MAPPINGS.SENSOR.temperature.min,
        temp_max: rows[0].querySelector('.val-max').value || MAPPINGS.SENSOR.temperature.max,
        hum_min: rows[1].querySelector('.val-min').value || MAPPINGS.SENSOR.humidity.min,
        hum_max: rows[1].querySelector('.val-max').value || MAPPINGS.SENSOR.humidity.max,
        light_min: rows[2].querySelector('.val-min').value || MAPPINGS.SENSOR.light.min,
        light_max: rows[2].querySelector('.val-max').value || MAPPINGS.SENSOR.light.max,
        id: newId
    };
    return rule;
}

// Gửi rule đến API Flask để lưu vào database
function saveRuleToDatabase(rule) {
    fetch('/api/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(rule)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error saving rule:', data.error);
        } else {
            console.log('Rule saved successfully:', data);
            alert('Rule đã được lưu vào database!');
        }
    })
    .catch(error => console.error('Error:', error));
}

// Cập nhật hàm saveRule để lưu vào database
function saveRule() {
    const r = readRuleFromModal();
    if (!r) return;
    console.log('Rule JSON:', JSON.stringify(r, null, 2));
    rules.push(r);
    renderRules();
    closeModal();
    saveRuleToDatabase(r); // Gửi rule đến API để lưu vào database
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
q('#btnSave').onclick = saveRule;

renderRules();
