// Tạo dữ liệu mẫu cho các loại cảm biến
export function generateRandomData(sensorType, timeRange, selectedDate) {
    const data = [];
    const date = new Date(selectedDate);
    let count = timeRange === 'day' ? 24 : timeRange === 'week' ? 7 : 30;
    
    // Phạm vi giá trị theo loại cảm biến
    const ranges = {
        humidity: { min: 0, max: 100, unit: '%' },
        temperature: { min: 15, max: 40, unit: '°C' },
        light: { min: 0, max: 1000, unit: 'lux' }
    };
    
    const { min, max, unit } = ranges[sensorType] || ranges.humidity;
    let baseValue = min + (max - min) * 0.3 + Math.random() * (max - min) * 0.4;
    
    for (let i = 0; i < count; i++) {
        let timestamp;
        let variation = Math.sin(i/count * Math.PI * 2) * (max - min) * 0.2;
        let randomFactor = (Math.random() - 0.5) * (max - min) * 0.1;
        
        let value = baseValue + variation + randomFactor;
        value = Math.max(min * 0.9, Math.min(max * 1.1, value));
        
        // Tạo giá trị cực trị ngẫu nhiên
        if (Math.random() > 0.95) value = max * 0.8 + Math.random() * max * 0.2;
        if (Math.random() > 0.95) value = min + Math.random() * min * 0.2;
        
        if (timeRange === 'day') {
            timestamp = `${i}:00`;
        } else {
            const day = new Date(date);
            day.setDate(date.getDate() + i);
            timestamp = day.toLocaleDateString('vi-VN');
        }
        
        data.push({ 
            timestamp, 
            value: Math.round(value * 10) / 10
        });
    }
    
    return {
        sensorType,
        labels: data.map(item => item.timestamp),
        values: data.map(item => item.value),
        unit
    };
}