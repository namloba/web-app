let currentChart;

// Cấu hình màu sắc và style cho từng loại cảm biến
const sensorStyles = {
    humidity: {
        color: 'rgb(75, 192, 192)',
        borderColor: 'rgb(75, 192, 192)',
        pointColor: (value) => {
            if (value > 80) return 'rgba(255, 99, 132, 0.7)';
            if (value < 30) return 'rgba(54, 162, 235, 0.7)';
            return 'rgba(75, 192, 192, 0.7)';
        },
        min: 0,
        max: 100
    },
    temperature: {
        color: 'rgb(255, 99, 132)',
        borderColor: 'rgb(255, 99, 132)',
        pointColor: (value) => {
            if (value > 35) return 'rgba(255, 69, 0, 0.7)';
            if (value < 15) return 'rgba(100, 149, 237, 0.7)';
            return 'rgba(255, 99, 132, 0.7)';
        },
        min: 10,
        max: 45
    },
    light: {
        color: 'rgb(255, 206, 86)',
        borderColor: 'rgb(255, 206, 86)',
        pointColor: (value) => {
            if (value > 800) return 'rgba(255, 215, 0, 0.7)';
            if (value < 200) return 'rgba(105, 105, 105, 0.7)';
            return 'rgba(255, 206, 86, 0.7)';
        },
        min: 0,
        max: 1200
    }
};

// Lấy tên hiển thị cho cảm biến
function getSensorName(sensorType) {
    const names = {
        humidity: 'Độ ẩm',
        temperature: 'Nhiệt độ',
        light: 'Ánh sáng'
    };
    return names[sensorType] || sensorType;
}

export function initChart(labels, data, sensorType) {
    const ctx = document.getElementById('sensorChart').getContext('2d');
    const style = sensorStyles[sensorType] || sensorStyles.humidity;
    
    if (currentChart) {
        currentChart.destroy();
    }
    
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${getSensorName(sensorType)}`,
                data: data,
                borderColor: style.borderColor,
                backgroundColor: style.color.replace(')', ', 0.1)'),
                tension: 0.1,
                pointStyle: 'circle',
                pointRadius: 8,
                pointHoverRadius: 12,
                pointHitRadius: 10,
                pointBorderColor: '#fff',
                pointBackgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex];
                    return style.pointColor(value);
                },
                pointBorderWidth: 2
            }]
        },
        options: getChartOptions(sensorType)
    });
}

function getChartOptions(sensorType) {
    const style = sensorStyles[sensorType] || sensorStyles.humidity;
    
    return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: false,
                min: style.min,
                max: style.max,
                title: {
                    display: true,
                    text: `${getSensorName(sensorType)} (${getUnit(sensorType)})`
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Thời gian'
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            }
        },
        plugins: {
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                callbacks: {
                    label: function(context) {
                        return ` ${context.dataset.label}: ${context.parsed.y}${getUnit(sensorType)}`;
                    }
                }
            },
            legend: {
                labels: {
                    usePointStyle: true,
                    padding: 20
                }
            }
        }
    };
}

function getUnit(sensorType) {
    const units = {
        humidity: '%',
        temperature: '°C',
        light: 'lux'
    };
    return units[sensorType] || '';
}

export function updateChart(labels, data, sensorType, unit) {
    if (currentChart) {
        currentChart.data.labels = labels;
        currentChart.data.datasets[0].data = data;
        currentChart.data.datasets[0].label = `${getSensorName(sensorType)} (${unit || getUnit(sensorType)})`;
        currentChart.options.scales.y.title.text = `${getSensorName(sensorType)} (${unit || getUnit(sensorType)})`;
        currentChart.update();
    }
}