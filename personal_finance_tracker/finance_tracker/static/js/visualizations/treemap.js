document.addEventListener('DOMContentLoaded', function () {
    const dataElement = document.getElementById('treemap-data');
    const incomeDataElement = document.getElementById('income-data');
    const expenseDataElement = document.getElementById('expense-data');
    const container = document.getElementById('treemap-chart');
    const viewInputs = document.querySelectorAll('input[name="viewType"]');
    const colorInputs = document.querySelectorAll('input[name="colorMode"]');


    if (!dataElement || !container) {
        console.error('Treemap data or container element not found.');
        if (container) container.innerHTML = '<p class="no-data-message">Error: Could not initialize treemap.</p>';
        return;
    }

    let currentData, incomeData, expenseData, combinedData;

    try {
        combinedData = JSON.parse(dataElement.textContent || '{}');
        incomeData = JSON.parse(incomeDataElement.textContent || '{}');
        expenseData = JSON.parse(expenseDataElement.textContent || '{}');
        currentData = combinedData;
    } catch (e) {
        console.error('Error parsing treemap data:', e);
        container.innerHTML = '<p class="no-data-message">Error parsing data.</p>';
        return;
    }

    function getColorScale(viewType, colorMode) {
        if (colorMode === 'type') {
            // Income vs Expense colors (red/green)
            return function(d) {
                if (viewType === 'both') {
                    const parentType = d.parent ? d.parent.data.type : d.data.type;
                    return parentType === 'income' ? '#4CAF50' : '#F44336';
                } else if (viewType === 'income') {
                    return '#4CAF50';
                } else if (viewType === 'expenses') {
                    return '#F44336';
                }
                return '#6a11cb';
            };
        } else {
            // Category colors (rainbow)
            const categoryColors = d3.scaleOrdinal(d3.schemeTableau10);
            return function(d) {
                return categoryColors(d.data.name);
            };
        }
    }

    function createTreemap(data, viewType = 'both', colorMode = 'type') {
        container.innerHTML = '';

        if (!data.children || data.children.length === 0) {
            container.innerHTML = '<p class="no-data-message">No transaction data available to display.</p>';
            return;
        }

        const width = container.clientWidth || 800;
        const height = 500;

        const svg = d3.select(container)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("font", "10px sans-serif");

        const treemapLayout = d3.treemap()
            .size([width, height])
            .paddingInner(3)
            .paddingOuter(6)
            .paddingTop(25)
            .round(true);

        const root = d3.hierarchy(data)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value);

        treemapLayout(root);

        const colorScale = getColorScale(viewType, colorMode);
        
        const tooltip = d3.select("body").append("div")
            .attr("class", "treemap-tooltip")
            .style("opacity", 0)
            .style("position", "absolute")
            .style("background", "rgba(0, 0, 0, 0.9)")
            .style("color", "white")
            .style("padding", "10px")
            .style("border-radius", "5px")
            .style("pointer-events", "none")
            .style("font-size", "13px")
            .style("z-index", "1000");

        // Create groups for each cell
        const cell = svg.selectAll("g")
            .data(root.leaves())
            .join("g")
            .attr("transform", d => `translate(${d.x0},${d.y0})`);

        // Add rectangles
        cell.append("rect")
            .attr("class", "treemap-cell")
            .attr("width", d => d.x1 - d.x0)
            .attr("height", d => d.y1 - d.y0)
            .attr("fill", d => colorScale(d))
            .style("stroke", "white")
            .style("stroke-width", "2px")
            .style("opacity", 0.8)
            .style("cursor", "pointer")
            .on("mouseover", function (event, d) {
                d3.select(this).style("opacity", 1);
                tooltip.transition().duration(200).style("opacity", 1);
                
                const parentType = d.parent ? d.parent.data.name : 'Unknown';
                const percentage = ((d.value / root.value) * 100).toFixed(1);
                
                tooltip.html(`
                    <strong>${d.data.name}</strong><br/>
                    Type: ${parentType}<br/>
                    Amount: $${d.value.toFixed(2)}<br/>
                    Percentage: ${percentage}%
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function () {
                d3.select(this).style("opacity", 0.8);
                tooltip.transition().duration(300).style("opacity", 0);
            });

        // Add labels
        cell.each(function(d) {
            const cellNode = d3.select(this);
            const cellWidth = d.x1 - d.x0;
            const cellHeight = d.y1 - d.y0;

            if (cellWidth > 50 && cellHeight > 30) {
                const nameLabel = cellNode.append("text")
                    .attr("class", "treemap-label")
                    .attr("x", 5)
                    .attr("y", 15)
                    .style("fill", "white")
                    .style("font-size", "12px")
                    .style("font-weight", "bold")
                    .style("text-shadow", "1px 1px 2px rgba(0,0,0,0.7)")
                    .text(d.data.name);

                if (cellHeight > 50) {
                    cellNode.append("text")
                        .attr("class", "treemap-label")
                        .attr("x", 5)
                        .attr("y", 32)
                        .style("fill", "white")
                        .style("font-size", "11px")
                        .style("text-shadow", "1px 1px 2px rgba(0,0,0,0.7)")
                        .text(`$${d.value.toFixed(2)}`);
                }

                // Simple text wrapping
                const textLength = nameLabel.node().getComputedTextLength();
                if (textLength > (cellWidth - 10)) {
                    let text = nameLabel.text();
                    while (nameLabel.node().getComputedTextLength() > (cellWidth - 15) && text.length > 0) {
                        text = text.slice(0, -1);
                        nameLabel.text(text + '...');
                    }
                }
            }
        });
    }

    function updateTreemap() {
        const viewType = document.querySelector('input[name="viewType"]:checked').value;
        const colorMode = document.querySelector('input[name="colorMode"]:checked').value;

        let dataToUse;
        switch(viewType) {
            case 'income':
                dataToUse = incomeData;
                break;
            case 'expenses':
                dataToUse = expenseData;
                break;
            case 'both':
            default:
                dataToUse = combinedData;
                break;
        }
        
        // Remove any existing tooltips
        d3.selectAll('.treemap-tooltip').remove();
        
        createTreemap(dataToUse, viewType, colorMode);
    }

    // Add event listeners to view type selectors
    viewInputs.forEach(input => {
        input.addEventListener('change', () => updateTreemap(input.value));
    });

    colorInputs.forEach(input => {
        input.addEventListener('change', updateTreemap);
    });

    // Initial render
    updateTreemap('both');
});