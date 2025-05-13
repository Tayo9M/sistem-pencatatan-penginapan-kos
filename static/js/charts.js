// This script handles client-side chart functionality using Chart.js

document.addEventListener('DOMContentLoaded', function() {
    // Check if we have a chart container
    const incomeExpenseCanvas = document.getElementById('incomeExpenseChart');
    if (incomeExpenseCanvas) {
        renderIncomeExpenseChart(incomeExpenseCanvas);
    }
    
    const occupancyRateCanvas = document.getElementById('occupancyRateChart');
    if (occupancyRateCanvas) {
        renderOccupancyRateChart(occupancyRateCanvas);
    }
    
    // Format all currency inputs
    document.querySelectorAll('.currency-input').forEach(function(input) {
        input.addEventListener('input', formatCurrency);
        // Don't format empty inputs on load
        // Only run formatting if input already has a value
        if (input.value) {
            formatCurrency({ target: input });
        }
    });
});

function renderIncomeExpenseChart(canvas) {
    // Get chart data from dataset
    const chartData = JSON.parse(canvas.dataset.chartData || '{}');
    if (!chartData.labels || !chartData.income || !chartData.expense) return;
    
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Pendapatan',
                    data: chartData.income,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: 'rgba(40, 167, 69, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Pengeluaran',
                    data: chartData.expense,
                    backgroundColor: 'rgba(255, 193, 7, 0.7)',
                    borderColor: 'rgba(255, 193, 7, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'Rp ' + value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += 'Rp ' + context.parsed.y.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

function renderOccupancyRateChart(canvas) {
    // Get chart data from dataset
    const chartData = JSON.parse(canvas.dataset.chartData || '{}');
    if (!chartData.labels || !chartData.datasets) return;
    
    const ctx = canvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + '%';
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

function formatCurrency(e) {
    let value = e.target.value;
    
    // Remove non-numeric characters
    value = value.replace(/[^\d]/g, '');
    
    // Format as Rupiah
    if (value !== '') {
        value = parseInt(value, 10).toLocaleString('id-ID');
        value = 'Rp ' + value;
    }
    
    // Don't set the value to "Rp " if input is empty or 0
    if (value === '' || value === '0' || value === 'Rp 0') {
        value = '';
    }
    
    e.target.value = value;
}
