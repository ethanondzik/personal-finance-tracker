document.addEventListener('DOMContentLoaded', function() {
    const dataElement = document.getElementById('heatmap-data');
    const container = document.getElementById('heatmap-display');
    const statsGrid = document.getElementById('statsGrid');
    const legendContainer = document.getElementById('legendContainer');
    const modeInputs = document.querySelectorAll('input[name="viewMode"]');

    if (!dataElement || !container) {
        container.innerHTML = '<p class="text-center text-danger">Unable to load heatmap data</p>';
        return;
    }

    const rawData = JSON.parse(dataElement.textContent || '{}');
    if (Object.keys(rawData).length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No transaction data available</p>';
        return;
    }

    const processedData = new Map();
    let totalTransactions = 0, totalIncome = 0, totalExpenses = 0;
    let dateRange = { min: null, max: null };

    Object.keys(rawData).forEach(dateStr => {
        const data = rawData[dateStr];
        processedData.set(dateStr, data);
        totalTransactions += data.count;
        totalIncome += data.income;
        totalExpenses += data.expense;
        
        const date = new Date(dateStr);
        if (!dateRange.min || date < dateRange.min) dateRange.min = date;
        if (!dateRange.max || date > dateRange.max) dateRange.max = date;
    });

    function updateStats() {
        const netBalance = totalIncome - totalExpenses;
        statsGrid.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${totalTransactions}</div>
                <div class="stat-label">Total Transactions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$${totalIncome.toFixed(0)}</div>
                <div class="stat-label">Total Income</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">$${totalExpenses.toFixed(0)}</div>
                <div class="stat-label">Total Expenses</div>
            </div>
            <div class="stat-card">
                <div class="stat-value ${netBalance >= 0 ? 'text-success' : 'text-danger'}">$${netBalance.toFixed(0)}</div>
                <div class="stat-label">Net Balance</div>
            </div>
        `;
    }

    function getColorScale(mode) {
        switch(mode) {
            case 'activity':
                return d3.scaleSequential(d3.interpolateBlues).domain([0, 15]);
            case 'balance':
                return d3.scaleSequential(d3.interpolateRdYlGn).domain([-500, 500]);
            case 'spending':
                return d3.scaleSequential(d3.interpolateReds).domain([0, 500]);
            case 'income':
                return d3.scaleSequential(d3.interpolateGreens).domain([0, 500]);
            default:
                return d3.scaleSequential(d3.interpolateBlues).domain([0, 10]);
        }
    }

    function getValue(data, mode) {
        if (!data) return 0;
        switch(mode) {
            case 'activity': return data.count;
            case 'balance': return data.income - data.expense;
            case 'spending': return data.expense;
            case 'income': return data.income;
            default: return data.count;
        }
    }

    function createLegend(mode) {
        const colors = getColorScale(mode);
        const values = mode === 'balance' ? [-500, -250, 0, 250, 500] : [0, 25, 50, 75, 100];
        
        legendContainer.innerHTML = values.map(val => `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${colors(val)}"></div>
                <span>${mode === 'balance' && val > 0 ? '+' : ''}${val}</span>
            </div>
        `).join('');
    }

    function renderHeatmap(mode = 'activity') {
        container.innerHTML = '';
        
        const yearStart = dateRange.min.getFullYear();
        const yearEnd = dateRange.max.getFullYear();
        const cellSize = 12;
        const cellGap = 3;
        const yearGap = 80;
        const yearLabelHeight = 40;
        const monthLabelHeight = 25;
        const dayLabelWidth = 30;
        
        const yearWidth = (cellSize + cellGap) * 53 + dayLabelWidth;
        const yearHeight = (cellSize + cellGap) * 7 + yearLabelHeight + monthLabelHeight;
        const totalWidth = yearWidth;
        const totalHeight = (yearEnd - yearStart + 1) * (yearHeight + yearGap);

        const svg = d3.select(container)
            .append('svg')
            .attr('class', 'heatmap-svg')
            .attr('width', totalWidth)
            .attr('height', totalHeight);

        const tooltip = d3.select('body').append('div')
            .attr('class', 'info-tooltip');

        const colorScale = getColorScale(mode);

        let yOffset = 0;
        for (let year = yearStart; year <= yearEnd; year++) {
            const yearGroup = svg.append('g')
                .attr('transform', `translate(0, ${yOffset})`);

            yearGroup.append('text')
                .attr('class', 'year-label')
                .attr('x', 20)
                .attr('y', 25)
                .attr('text-anchor', 'start')
                .text(year);

            const dataGroup = yearGroup.append('g')
                .attr('transform', `translate(0, ${yearLabelHeight})`);

            const yearData = d3.timeDays(new Date(year, 0, 1), new Date(year + 1, 0, 1));

            dataGroup.selectAll('.day-square')
                .data(yearData)
                .enter().append('rect')
                .attr('class', 'day-square')
                .attr('width', cellSize)
                .attr('height', cellSize)
                .attr('x', d => d3.timeWeek.count(d3.timeYear(d), d) * (cellSize + cellGap) + dayLabelWidth)
                .attr('y', d => d.getDay() * (cellSize + cellGap) + monthLabelHeight)
                .attr('fill', d => {
                    const dateStr = d3.timeFormat('%Y-%m-%d')(d);
                    const data = processedData.get(dateStr);
                    return colorScale(getValue(data, mode));
                })
                .on('mouseover', function(event, d) {
                    const dateStr = d3.timeFormat('%Y-%m-%d')(d);
                    const data = processedData.get(dateStr);
                    
                    tooltip.transition().duration(200).style('opacity', 1);
                    tooltip.html(`
                        <strong>${d3.timeFormat('%B %d, %Y')(d)}</strong><br/>
                        Transactions: ${data ? data.count : 0}<br/>
                        Income: $${data ? data.income.toFixed(2) : '0.00'}<br/>
                        Expenses: $${data ? data.expense.toFixed(2) : '0.00'}<br/>
                        Net: $${data ? (data.income - data.expense).toFixed(2) : '0.00'}
                    `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px');
                })
                .on('mouseout', function() {
                    tooltip.transition().duration(300).style('opacity', 0);
                });

            const months = d3.timeMonths(new Date(year, 0, 1), new Date(year + 1, 0, 1));
            dataGroup.selectAll('.month-text')
                .data(months)
                .enter().append('text')
                .attr('class', 'month-text')
                .attr('x', d => d3.timeWeek.count(d3.timeYear(d), d) * (cellSize + cellGap) + dayLabelWidth + cellSize/2)
                .attr('y', 15)
                .attr('text-anchor', 'middle')
                .text(d3.timeFormat('%b'));

            const dayLabels = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
            dataGroup.selectAll('.day-text')
                .data(dayLabels)
                .enter().append('text')
                .attr('class', 'day-text')
                .attr('x', 20)
                .attr('y', (d, i) => i * (cellSize + cellGap) + monthLabelHeight + cellSize/2 + 3)
                .attr('text-anchor', 'middle')
                .text(d => d);

            yOffset += yearHeight + yearGap;
        }

        createLegend(mode);
    }

    modeInputs.forEach(input => {
        input.addEventListener('change', () => renderHeatmap(input.value));
    });

    updateStats();
    renderHeatmap();
});