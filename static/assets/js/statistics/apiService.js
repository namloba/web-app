import { generateRandomData } from './dataGenerator.js';

// Hàm giả lập API cho nhiều loại cảm biến
export async function fetchSensorData(sensorType, timeRange, selectedDate) {
    try {
        const res = await fetch(`/api/statistics/${sensorType}?timeRange=${timeRange}&date=${selectedDate}`);
        const data = await res.json();

        return {
            sensorType,
            labels: data.map(d => d.time),
            values: data.map(d => d.value),
            unit: getUnit(sensorType)
        };
    } catch (err) {
        console.error("Lỗi lấy dữ liệu từ Flask:", err);
        return {
            sensorType,
            labels: [],
            values: [],
            unit: getUnit(sensorType)
        };
    }
}

function getUnit(sensorType) {
    const units = {
        humidity: '%',
        temperature: '°C',
        light: 'lux'
    };
    return units[sensorType] || '';
}
