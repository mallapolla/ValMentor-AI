// Dashboard charts rendering logic
function initDashboardCharts(valuesJSON, labelsJSON) {
    const ctx = document.getElementById("learning-activity-chart");
    if (!ctx) return;

    try {
        const values = JSON.parse(valuesJSON);
        const labels = JSON.parse(labelsJSON);

        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Minutes Studied',
                    data: values,
                    backgroundColor: 'rgba(6, 182, 212, 0.45)',
                    borderColor: '#06B6D4',
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#94a3b8'
                        }
                    }
                }
            }
        });
    } catch (e) {
        console.error("Failed to render dashboard charts: ", e);
    }
}
