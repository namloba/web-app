// import { initChart, updateChart } from './chartManager.js';
// import { fetchSensorData } from './apiService.js';
// import { generateRandomData } from './dataGenerator.js';

// document.addEventListener('DOMContentLoaded', function() {
//     const sensorSelect = document.getElementById('sensorSelect');
//     const timeRangeSelect = document.getElementById('timeRange');
//     const datePicker = document.getElementById('datePicker');
//     const fetchButton = document.getElementById('fetchData');
//     const generateRandomBtn = document.getElementById('generateRandom');
    
//     // Đặt ngày mặc định là hôm nay
//     const today = new Date().toISOString().split('T')[0];
//     datePicker.value = today;
    
//     // Khởi tạo biểu đồ với dữ liệu rỗng
//     initChart([], [], 'humidity');
    
//     // Xử lý sự kiện khi nhấn nút lấy dữ liệu
//     fetchButton.addEventListener('click', async function() {
//         const sensorType = sensorSelect.value;
//         const timeRange = timeRangeSelect.value;
//         const selectedDate = datePicker.value;
        
//         if (!selectedDate) {
//             alert('Vui lòng chọn ngày');
//             return;
//         }
        
//         const data = await fetchSensorData(sensorType, timeRange, selectedDate);
//         updateChart(data.labels, data.values, sensorType, data.unit);
//     });
    
//     // Xử lý sự kiện khi nhấn nút tạo dữ liệu ngẫu nhiên
//     generateRandomBtn.addEventListener('click', function() {
//         const sensorType = sensorSelect.value;
//         const timeRange = timeRangeSelect.value;
//         const selectedDate = datePicker.value;
        
//         if (!selectedDate) {
//             alert('Vui lòng chọn ngày');
//             return;
//         }
        
//         const randomData = generateRandomData(sensorType, timeRange, selectedDate);
//         updateChart(randomData.labels, randomData.values, sensorType, randomData.unit);
//     });
    
//     // Lấy dữ liệu ban đầu
//     fetchSensorData('humidity', 'day', today)
//         .then(data => updateChart(data.labels, data.values, 'humidity', data.unit));
// });

import { initChart, updateChart } from './chartManager.js';
import { fetchSensorData } from './apiService.js';
import { generateRandomData } from './dataGenerator.js';

document.addEventListener('DOMContentLoaded', function() {
    const sensorSelect = document.getElementById('sensorSelect');
    const timeRangeSelect = document.getElementById('timeRange');
    const datePicker = document.getElementById('datePicker');
    const generateRandomBtn = document.getElementById('generateRandom');

    // Đặt ngày mặc định là hôm nay
    const today = new Date().toISOString().split('T')[0];
    datePicker.value = today;

    // Khởi tạo biểu đồ với dữ liệu rỗng
    initChart([], [], 'humidity');

    // ✅ Gắn sự kiện cho nút DỮ LIỆU NGẪU NHIÊN
    generateRandomBtn.addEventListener('click', function () {
        const sensorType = sensorSelect.value;
        const timeRange = timeRangeSelect.value;
        const selectedDate = datePicker.value;

        if (!selectedDate) {
            alert('Vui lòng chọn ngày');
            return;
        }

        const randomData = generateRandomData(sensorType, timeRange, selectedDate);
        updateChart(randomData.labels, randomData.values, sensorType, randomData.unit);
    });

    // ✅ KHÔNG gọi fetchSensorData vì bạn đã bỏ nút lấy dữ liệu thật
    // Bạn có thể hiển thị dữ liệu ngẫu nhiên mặc định lúc vào trang nếu muốn:
    const initialData = generateRandomData('humidity', 'day', today);
    updateChart(initialData.labels, initialData.values, 'humidity', initialData.unit);
});
