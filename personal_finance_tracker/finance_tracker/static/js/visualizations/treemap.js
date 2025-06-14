document.addEventListener('DOMContentLoaded', function () {
    const dataElement = document.getElementById('treemap-data');
    const container = document.getElementById('treemap-chart');

    if (!dataElement || !container) {
        console.error('Treemap data or container element not found.');
        if (container) container.innerHTML = '<p class="no-data-message">Error: Could not initialize treemap.</p>';
        return;
    }

    try {
        const treemapData = JSON.parse(dataElement.textContent || '{}');

        if (!treemapData.children || treemapData.children.length === 0) {
            container.innerHTML = '<p class="no-data-message">No expense data available to display in the treemap.</p>';
            return;
        }

        const width = container.clientWidth || 800;
        const height = container.clientHeight || 500;

        const svg = d3.select(container)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("font", "10px sans-serif");

        const treemapLayout = d3.treemap()
            .size([width, height])
            .paddingInner(2) // Padding between sibling cells
            .paddingOuter(5) // Padding around the root
            .paddingTop(20) // Padding for the root label if you add one
            .round(true);

        const root = d3.hierarchy(treemapData)
            .sum(d => d.value) // Size of leaves is based on 'value'
            .sort((a, b) => b.value - a.value); // Sort by value, descending

        treemapLayout(root);

        const color = d3.scaleOrdinal(d3.schemeTableau10); // A nice default color scheme

        const cell = svg.selectAll("g")
            .data(root.leaves()) // We only draw the leaves (actual categories)
            .join("g")
            .attr("transform", d => `translate(${d.x0},${d.y0})`);

        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "treemap-tooltip");

        cell.append("rect")
            .attr("class", "treemap-cell")
            .attr("width", d => d.x1 - d.x0)
            .attr("height", d => d.y1 - d.y0)
            .attr("fill", d => d.data.color ? d.data.color : color(d.data.name)) // Use provided color or scale
            .on("mouseover", function (event, d) {
                d3.select(this).style("opacity", 0.8);
                tooltip.transition().duration(200).style("opacity", 1);
                tooltip.html(`
                    <strong>${d.data.name}</strong><br/>
                    Amount: $${d.value.toFixed(2)}<br/>
                    Percentage: ${((d.value / root.value) * 100).toFixed(1)}%
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
            })
            .on("mouseout", function () {
                d3.select(this).style("opacity", 1);
                tooltip.transition().duration(300).style("opacity", 0);
            });

        // Add labels to cells
        cell.each(function(d) {
            const cellNode = d3.select(this);
            const width = d.x1 - d.x0;
            const height = d.y1 - d.y0;

            // Add text for category name
            const nameLabel = cellNode.append("text")
                .attr("class", "treemap-label name-label")
                .attr("x", 5) // Small padding from left
                .attr("y", 15) // Position for the name
                .text(d.data.name)
                .style("font-size", "12px")
                .style("font-weight", "bold");
            
            // Add text for value (amount)
            const valueLabel = cellNode.append("text")
                .attr("class", "treemap-label value-label")
                .attr("x", 5) // Small padding from left
                .attr("y", 32) // Position for the value, below the name
                .text(`$${d.value.toFixed(2)}`)
                .style("font-size", "11px");

            // Simple text wrapping / clipping logic 
            function wrapText(textElement, maxWidth) {
                let textLength = textElement.node().getComputedTextLength();
                let text = textElement.text();
                while (textLength > (maxWidth - 10) && text.length > 0) { // -10 for padding
                    text = text.slice(0, -1);
                    textElement.text(text + '...');
                    textLength = textElement.node().getComputedTextLength();
                }
            }
            
            if (width > 20 && height > 40) { // Only show labels if cell is reasonably sized
                 wrapText(nameLabel, width);
                 if (height > 55) { // Only show value if there's enough space below name
                    wrapText(valueLabel, width);
                 } else {
                    valueLabel.remove(); // Remove value if not enough space
                 }
            } else {
                nameLabel.remove();
                valueLabel.remove();
            }
        });


    } catch (e) {
        console.error('Error rendering D3 treemap:', e);
        if (container) container.innerHTML = '<p class="no-data-message">An error occurred while rendering the treemap.</p>';
    }
});