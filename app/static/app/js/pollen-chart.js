document.addEventListener('DOMContentLoaded', () => {
    const chartDataElement = document.getElementById('chart-data');
    if (!chartDataElement) return;

    const datasets = JSON.parse(chartDataElement.textContent);

    const ctx = document.getElementById('pollenChart').getContext('2d');

    new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: false,
            parsing: { xAxisKey: 'x', yAxisKey: 'y' },
            scales: {
                x: {
                    title: { display: true, text: 'Время' }
                },
                y: {
                    title: { display: true, text: 'Концентрация пыльцы' },
                    beginAtZero: true
                }
            }
        }
    });
});
