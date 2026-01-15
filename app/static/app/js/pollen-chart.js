document.addEventListener('DOMContentLoaded', () => {
    const chartDataElement = document.getElementById('chart-data');
    if (!chartDataElement) return;

    const chartData = JSON.parse(chartDataElement.textContent);

    const labels = chartData.map(item => item.label);

    const values = chartData.map(item => item.value);

    const ctx = document.getElementById('pollenChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Концентрация пыльцы (grains/m³)',
                data: values,
                borderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
});
