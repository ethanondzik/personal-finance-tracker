document.addEventListener('DOMContentLoaded', function() {
    const incomeData = JSON.parse(document.getElementById('income-data').textContent || '[]');
    const expenseData = JSON.parse(document.getElementById('expense-data').textContent || '[]');
    const accountsData = JSON.parse(document.getElementById('accounts-data').textContent || '[]');

    // Calculate totals
    const totalIncome = incomeData.reduce((sum, item) => sum + item.amount, 0);
    const totalExpenses = expenseData.reduce((sum, item) => sum + item.amount, 0);
    const netFlow = totalIncome - totalExpenses;

    // Update the net flow display
    updateNetFlowDisplay(netFlow);

    createSankeyVisualization(incomeData, expenseData, accountsData, totalIncome, totalExpenses);
});

function updateNetFlowDisplay(netFlow) {
    // Find the net flow stat card
    const statCards = document.querySelectorAll('.stat-card');
    let netCard = null;
    
    statCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (text.includes('net flow')) {
            netCard = card;
        }
    });

    if (netCard) {
        const h3Element = netCard.querySelector('h3');
        if (h3Element) {
            // Update the text content
            h3Element.textContent = `$${netFlow.toFixed(2)}`;
            
            // Update styling based on positive/negative
            h3Element.className = netFlow >= 0 ? 'positive' : 'negative';
            
            // Update the parent card class
            netCard.classList.remove('income', 'expense', 'positive', 'negative');
            netCard.classList.add(netFlow >= 0 ? 'positive' : 'negative');
        }
    }
}

function createSankeyVisualization(incomeData, expenseData, accountsData, totalIncome, totalExpenses) {
    const container = document.getElementById('sankey-chart');
    
    // Clear any existing content
    container.innerHTML = '';
    
    if (incomeData.length === 0 && expenseData.length === 0) {
        container.innerHTML = '<div class="no-data">No transaction data available for visualization</div>';
        return;
    }

    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const width = 1000 - margin.left - margin.right;
    const height = 600 - margin.top - margin.bottom;

    const svg = d3.select(container)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const sankey = d3.sankey()
        .nodeWidth(20)
        .nodePadding(10)
        .extent([[1, 1], [width - 1, height - 6]]);

    // Build nodes and links with better data handling
    const nodes = [];
    const links = [];
    
    // Add income source nodes
    incomeData.forEach((d, i) => {
        nodes.push({
            name: d.category,
            category: 'income',
            value: d.amount
        });
    });
    
    // Add central hub node
    const hubIndex = incomeData.length;
    nodes.push({
        name: 'Available Funds',
        category: 'transfer',
        value: totalIncome
    });
    
    // Add expense category nodes
    expenseData.forEach((d, i) => {
        nodes.push({
            name: d.category,
            category: 'expense',
            value: d.amount
        });
    });
    
    // Create links from income to hub
    incomeData.forEach((d, i) => {
        links.push({
            source: i,
            target: hubIndex,
            value: d.amount
        });
    });
    
    // Create links from hub to expenses
    expenseData.forEach((d, i) => {
        links.push({
            source: hubIndex,
            target: hubIndex + 1 + i,
            value: d.amount
        });
    });

    const graph = sankey({nodes, links});

    const color = d3.scaleOrdinal()
        .domain(['income', 'transfer', 'expense'])
        .range(['#4CAF50', '#2196F3', '#F44336']);

    // Create tooltip
    const tooltip = d3.select('body').append('div')
        .attr('class', 'sankey-tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background', 'rgba(0, 0, 0, 0.8)')
        .style('color', 'white')
        .style('padding', '10px')
        .style('border-radius', '5px')
        .style('pointer-events', 'none')
        .style('z-index', '1000')
        .style('font-size', '13px')
        .style('max-width', '200px')
        .style('box-shadow', '0 4px 8px rgba(0,0,0,0.3)');

    // Draw links
    svg.append('g')
        .selectAll('.link')
        .data(graph.links)
        .enter().append('path')
        .attr('class', 'sankey-link')
        .attr('d', d3.sankeyLinkHorizontal())
        .attr('stroke', d => color(d.source.category))
        .attr('stroke-width', d => Math.max(1, d.width))
        .style('fill', 'none')
        .style('stroke-opacity', 0.6)
        .style('transition', 'stroke-opacity 0.3s')
        .on('mouseover', function(event, d) {
            d3.select(this).style('stroke-opacity', 0.8);
            tooltip.transition().duration(200).style('opacity', 1);
            tooltip.html(`
                <strong>${d.source.name} → ${d.target.name}</strong><br/>
                Amount: $${d.value.toFixed(2)}<br/>
                Percentage: ${totalIncome > 0 ? ((d.value / totalIncome) * 100).toFixed(1) : 0}%
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this).style('stroke-opacity', 0.6);
            tooltip.transition().duration(300).style('opacity', 0);
        });

    // Draw nodes
    svg.append('g')
        .selectAll('.node')
        .data(graph.nodes)
        .enter().append('g')
        .attr('class', 'sankey-node')
        .attr('transform', d => `translate(${d.x0},${d.y0})`)
        .append('rect')
        .attr('height', d => d.y1 - d.y0)
        .attr('width', d => d.x1 - d.x0)
        .attr('fill', d => color(d.category))
        .style('stroke', '#fff')
        .style('stroke-width', '2px')
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
            tooltip.transition().duration(200).style('opacity', 1);
            tooltip.html(`
                <strong>${d.name}</strong><br/>
                Amount: $${d.value.toFixed(2)}<br/>
                Category: ${d.category}<br/>
                Percentage: ${totalIncome > 0 ? ((d.value / totalIncome) * 100).toFixed(1) : 0}%
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
            tooltip.transition().duration(300).style('opacity', 0);
        });

    // Add labels
    svg.selectAll('.sankey-node')
        .append('text')
        .attr('x', d => d.x0 < width / 2 ? 25 : -6)
        .attr('y', d => (d.y1 - d.y0) / 2)
        .attr('dy', '0.35em')
        .attr('text-anchor', d => d.x0 < width / 2 ? 'start' : 'end')
        .text(d => d.name)
        .style('font-size', '12px')
        .style('font-weight', '500')
        .style('fill', '#333')
        .style('pointer-events', 'none');

    // Clean up any existing tooltips when page unloads
    window.addEventListener('beforeunload', function() {
        d3.selectAll('.sankey-tooltip').remove();
    });
}