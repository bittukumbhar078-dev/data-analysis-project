document.querySelectorAll('.data-chart').forEach(function (canvas) {
    const data = JSON.parse(canvas.dataset.chart);
    const card = canvas.closest('.chart-card');
    const selection = card.querySelector('.chart-selection');
    const typeButtons = card.querySelectorAll('.chart-type-button');
    let chart;

    function colorList(length) {
        const colors = ['#3b63f3', '#6282f5', '#829af8', '#a1b3fa', '#c0ccfc', '#5e7ded', '#7891f5', '#98acf8'];
        return Array.from({ length: length }, function (_, index) { return colors[index % colors.length]; });
    }

    function makeChart(type) {
        if (chart) chart.destroy();
        const isScatter = data.type === 'scatter';
        const activeType = isScatter ? 'scatter' : type;
        const values = isScatter ? data.points : data.values;
        const colors = colorList((data.labels || []).length);

        chart = new Chart(canvas, {
            type: activeType,
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: data.title,
                    data: values,
                    backgroundColor: activeType === 'doughnut' ? colors : '#6383f5',
                    borderColor: activeType === 'doughnut' ? '#ffffff' : '#3b63f3',
                    borderWidth: activeType === 'doughnut' ? 2 : 2,
                    borderRadius: activeType === 'bar' ? 5 : 0,
                    pointRadius: activeType === 'scatter' ? 4 : 3,
                    pointHoverRadius: 7,
                    tension: .35
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: data.horizontal && activeType === 'bar' ? 'y' : 'x',
                interaction: { mode: activeType === 'doughnut' ? 'nearest' : 'index', intersect: false },
                plugins: {
                    legend: { display: activeType === 'doughnut', position: 'bottom', labels: { boxWidth: 10, padding: 12 } },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                if (activeType === 'scatter') return ` (${context.raw.x}, ${context.raw.y})`;
                                const total = data.values.reduce(function (sum, value) { return sum + Number(value); }, 0);
                                const percent = total ? ((context.raw / total) * 100).toFixed(1) : 0;
                                return ` ${context.dataset.label}: ${Number(context.raw).toLocaleString()} (${percent}%)`;
                            }
                        }
                    }
                },
                onClick: function (event, elements) {
                    if (!elements.length) return;
                    const point = elements[0];
                    if (activeType === 'scatter') {
                        const item = data.points[point.index];
                        selection.textContent = `Selected point: X = ${item.x.toLocaleString()}, Y = ${item.y.toLocaleString()}.`;
                    } else {
                        const label = data.labels[point.index];
                        const value = data.values[point.index];
                        const total = data.values.reduce(function (sum, current) { return sum + Number(current); }, 0);
                        selection.textContent = `${label}: ${Number(value).toLocaleString()} (${((value / total) * 100).toFixed(1)}% of displayed total).`;
                    }
                },
                scales: activeType === 'doughnut' ? {} : (activeType === 'scatter' ? {
                    x: { type: 'linear', title: { display: true, text: 'X value' } },
                    y: { title: { display: true, text: 'Y value' } }
                } : {
                    y: { beginAtZero: true, grid: { color: '#edf0f5' } },
                    x: { grid: { display: false }, ticks: { maxRotation: 35, minRotation: 0 } }
                })
            }
        });
    }

    const firstType = data.type === 'line' ? 'line' : 'bar';
    makeChart(firstType);
    typeButtons.forEach(function (button) {
        button.classList.toggle('active', button.dataset.type === firstType);
    });

    typeButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            typeButtons.forEach(function (item) { item.classList.remove('active'); });
            button.classList.add('active');
            selection.textContent = `Showing ${button.textContent.toLowerCase()} view. Hover or click a value for details.`;
            makeChart(button.dataset.type);
        });
    });

    card.querySelector('.chart-expand-button').addEventListener('click', function () {
        card.classList.toggle('expanded');
        this.querySelector('i').className = card.classList.contains('expanded') ? 'bi bi-fullscreen-exit' : 'bi bi-arrows-fullscreen';
        setTimeout(function () { chart.resize(); }, 50);
    });
});
