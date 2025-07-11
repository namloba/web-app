import { generateRandomData } from './dataGenerator.js';

// Hàm giả lập API cho nhiều loại cảm biến
export async function fetchSensorData(sensorType, timeRange, selectedDate) {
    console.log(`Fetching ${sensorType} data for ${timeRange} on ${selectedDate}`);
    
    // Giả lập delay của API
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Trả về dữ liệu ngẫu nhiên cho cảm biến cụ thể
    return generateRandomData(sensorType, timeRange, selectedDate);
}