document.addEventListener('DOMContentLoaded', function() {
    const networkDataElement = document.getElementById('network-data');
    const networkStatsElement = document.getElementById('network-stats');
    const container = document.getElementById('network-chart');

    if (!networkDataElement || !container) {
        console.error('Network data or container element not found.');
        if (container) {
            container.innerHTML = '<p class="text-center text-danger">Unable to load network data</p>';
        }
        return;
    }

    let networkData, networkStats;
    
    try {
        networkData = JSON.parse(networkDataElement.textContent || '{}');
        networkStats = JSON.parse(networkStatsElement.textContent || '{}');
    } catch (e) {
        console.error('Error parsing network data:', e);
        container.innerHTML = '<p class="text-center text-danger">Error parsing network data</p>';
        return;
    }

    if (!networkData.nodes || networkData.nodes.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No network data available</p>';
        return;
    }

    // Initialize the network visualization
    initializeNetwork(networkData, networkStats);
});

function initializeNetwork(data, stats) {
    const container = document.getElementById('network-chart');
    
    // Clear loading spinner
    container.innerHTML = '';
    
    // Set up dimensions
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;
    
    // Create SVG
    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .style('background', 'transparent');
    
    // Add zoom behavior
    const g = svg.append('g');
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Add zoom controls
    addZoomControls(svg, zoom, width, height);
    
    // Create tooltip
    const tooltip = createTooltip();
    
    // Prepare data
    const nodes = data.nodes.map(d => Object.assign({}, d));
    const links = data.links.map(d => Object.assign({}, d));
    
    // Create simulation
    const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.size + 5));
    
    // Draw links
    const link = g.append('g')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('class', 'network-link')
        .attr('stroke-width', d => Math.max(1, d.width / 3))
        .on('mouseover', (event, d) => showLinkTooltip(event, d, tooltip))
        .on('mouseout', () => hideTooltip(tooltip));
    
    // Draw nodes
    const node = g.append('g')
        .selectAll('circle')
        .data(nodes)
        .join('circle')
        .attr('class', d => `network-node ${d.type} ${d.category_type || ''}`)
        .attr('r', d => d.size)
        .on('mouseover', (event, d) => showNodeTooltip(event, d, tooltip))
        .on('mouseout', () => hideTooltip(tooltip))
        .call(drag(simulation));
    
    // Add labels
    const labels = g.append('g')
        .selectAll('text')
        .data(nodes)
        .join('text')
        .attr('class', 'network-label')
        .text(d => d.name.length > 12 ? d.name.substring(0, 12) + '...' : d.name)
        .attr('dy', d => d.size + 15);
    
    // Update positions on simulation tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    // Control handlers
    setupControlHandlers(simulation, nodes, links, { node, link, labels }, tooltip);
    
    // Calculate and display insights
    calculateNetworkInsights(nodes, links);
    
    // Store references for later use
    window.networkVisualization = {
        svg, g, zoom, simulation, nodes, links, 
        elements: { node, link, labels },
        tooltip, width, height
    };
}

function addZoomControls(svg, zoom, width, height) {
    const controls = svg.append('g')
        .attr('class', 'zoom-controls')
        .attr('transform', `translate(${width - 60}, 20)`);
    
    // Zoom in button
    controls.append('rect')
        .attr('class', 'zoom-btn')
        .attr('width', 40)
        .attr('height', 40)
        .attr('rx', 6)
        .attr('fill', 'rgba(255, 255, 255, 0.9)')
        .attr('stroke', '#d1d5db')
        .style('cursor', 'pointer')
        .on('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 1.5);
        });
    
    controls.append('text')
        .attr('x', 20)
        .attr('y', 25)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .text('+')
        .style('font-size', '18px')
        .style('font-weight', 'bold')
        .style('pointer-events', 'none');
    
    // Zoom out button
    controls.append('rect')
        .attr('class', 'zoom-btn')
        .attr('width', 40)
        .attr('height', 40)
        .attr('y', 45)
        .attr('rx', 6)
        .attr('fill', 'rgba(255, 255, 255, 0.9)')
        .attr('stroke', '#d1d5db')
        .style('cursor', 'pointer')
        .on('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 0.75);
        });
    
    controls.append('text')
        .attr('x', 20)
        .attr('y', 70)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .text('−')
        .style('font-size', '18px')
        .style('font-weight', 'bold')
        .style('pointer-events', 'none');
}

function createTooltip() {
    return d3.select('body').append('div')
        .attr('class', 'network-tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('pointer-events', 'none');
}

function showNodeTooltip(event, d, tooltip) {
    let content = `<strong>${d.name}</strong><br/>`;
    content += `Type: ${d.type.charAt(0).toUpperCase() + d.type.slice(1)}<br/>`;
    
    if (d.type === 'account') {
        content += `Balance: $${d.balance.toFixed(2)}<br/>`;
        content += `Account Type: ${d.account_type}`;
    } else if (d.type === 'category') {
        content += `Total Volume: $${d.total_volume.toFixed(2)}<br/>`;
        content += `Category Type: ${d.category_type}`;
    }
    
    tooltip.transition().duration(200).style('opacity', 1);
    tooltip.html(content)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px');
}

function showLinkTooltip(event, d, tooltip) {
    const sourceName = d.source.name || d.source.id;
    const targetName = d.target.name || d.target.id;
    
    let content = `<strong>${sourceName} → ${targetName}</strong><br/>`;
    content += `Total Amount: $${d.value.toFixed(2)}<br/>`;
    content += `Transactions: ${d.transaction_count}<br/>`;
    content += `Income: $${d.income_amount.toFixed(2)}<br/>`;
    content += `Expenses: $${d.expense_amount.toFixed(2)}`;
    
    tooltip.transition().duration(200).style('opacity', 1);
    tooltip.html(content)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 10) + 'px');
}

function hideTooltip(tooltip) {
    tooltip.transition().duration(300).style('opacity', 0);
}

function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }
    
    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }
    
    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }
    
    return d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended);
}

function setupControlHandlers(simulation, nodes, links, elements, tooltip) {
    // Layout control
    document.getElementById('layoutSelect').addEventListener('change', (e) => {
        changeLayout(e.target.value, simulation, nodes, elements);
    });
    
    // Node size control
    document.getElementById('nodeSizeSelect').addEventListener('change', (e) => {
        updateNodeSizes(e.target.value, nodes, elements.node);
    });
    
    // Link width control
    document.getElementById('linkWidthSelect').addEventListener('change', (e) => {
        updateLinkWidths(e.target.value, links, elements.link);
    });
    
    // Color scheme control
    document.getElementById('colorSchemeSelect').addEventListener('change', (e) => {
        updateColorScheme(e.target.value, nodes, elements.node);
    });
    
    // Reset zoom
    document.getElementById('resetZoom').addEventListener('click', () => {
        const viz = window.networkVisualization;
        viz.svg.transition().duration(750).call(viz.zoom.transform, d3.zoomIdentity);
    });
    
    // Center network
    document.getElementById('centerNetwork').addEventListener('click', () => {
        simulation.alpha(0.3).restart();
    });
    
    // Export network
    document.getElementById('exportNetwork').addEventListener('click', () => {
        exportNetworkAsPNG();
    });
}

function changeLayout(layoutType, simulation, nodes, elements) {
    simulation.stop();
    
    switch(layoutType) {
        case 'circular':
            const radius = Math.min(window.networkVisualization.width, window.networkVisualization.height) / 3;
            nodes.forEach((d, i) => {
                const angle = (i / nodes.length) * 2 * Math.PI;
                d.fx = window.networkVisualization.width / 2 + radius * Math.cos(angle);
                d.fy = window.networkVisualization.height / 2 + radius * Math.sin(angle);
            });
            break;
            
        case 'hierarchical':
            const accountNodes = nodes.filter(d => d.type === 'account');
            const categoryNodes = nodes.filter(d => d.type === 'category');
            
            accountNodes.forEach((d, i) => {
                d.fx = (i + 1) * (window.networkVisualization.width / (accountNodes.length + 1));
                d.fy = window.networkVisualization.height * 0.2;
            });
            
            categoryNodes.forEach((d, i) => {
                d.fx = (i + 1) * (window.networkVisualization.width / (categoryNodes.length + 1));
                d.fy = window.networkVisualization.height * 0.8;
            });
            break;
            
        case 'force':
        default:
            nodes.forEach(d => {
                d.fx = null;
                d.fy = null;
            });
            break;
    }
    
    simulation.alpha(0.3).restart();
}

function updateNodeSizes(sizeMode, nodes, nodeElements) {
    nodeElements.transition().duration(500)
        .attr('r', d => {
            switch(sizeMode) {
                case 'balance':
                    return d.type === 'account' ? 
                        Math.max(8, Math.min(30, d.balance / 100)) : 
                        Math.max(8, Math.min(30, d.total_volume / 50));
                case 'uniform':
                    return 15;
                case 'volume':
                default:
                    return d.size;
            }
        });
}

function updateLinkWidths(widthMode, links, linkElements) {
    linkElements.transition().duration(500)
        .attr('stroke-width', d => {
            switch(widthMode) {
                case 'count':
                    return Math.max(1, d.transaction_count / 2);
                case 'uniform':
                    return 2;
                case 'amount':
                default:
                    return Math.max(1, d.width / 3);
            }
        });
}

function updateColorScheme(colorMode, nodes, nodeElements) {
    nodeElements.transition().duration(500)
        .attr('fill', d => {
            switch(colorMode) {
                case 'activity':
                    const activity = d.type === 'account' ? d.balance : d.total_volume;
                    return d3.interpolateViridis(activity / 1000);
                case 'balance':
                    if (d.type === 'account') {
                        return d.balance > 1000 ? '#10b981' : d.balance > 0 ? '#3b82f6' : '#ef4444';
                    } else {
                        return d.total_volume > 500 ? '#10b981' : '#8b5cf6';
                    }
                case 'type':
                default:
                    if (d.type === 'account') return '#3b82f6';
                    if (d.category_type === 'income') return '#10b981';
                    if (d.category_type === 'expense') return '#ef4444';
                    return '#8b5cf6';
            }
        });
}

function calculateNetworkInsights(nodes, links) {
    const totalNodes = nodes.length;
    const totalLinks = links.length;
    const maxPossibleLinks = totalNodes * (totalNodes - 1) / 2;
    const networkDensity = ((totalLinks / maxPossibleLinks) * 100).toFixed(1);
    const avgConnections = (totalLinks * 2 / totalNodes).toFixed(1);
    
    document.getElementById('networkDensity').textContent = `${networkDensity}%`;
    document.getElementById('avgConnections').textContent = avgConnections;
}

function exportNetworkAsPNG() {
    const viz = window.networkVisualization;
    const svgElement = viz.svg.node();
    
    // Create canvas
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = viz.width;
    canvas.height = viz.height;
    
    // Convert SVG to image
    const data = new XMLSerializer().serializeToString(svgElement);
    const svgBlob = new Blob([data], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    
    const img = new Image();
    img.onload = function() {
        context.fillStyle = 'white';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.drawImage(img, 0, 0);
        
        // Download
        const link = document.createElement('a');
        link.download = 'financial-network.png';
        link.href = canvas.toDataURL();
        link.click();
        
        URL.revokeObjectURL(url);
    };
    img.src = url;
}