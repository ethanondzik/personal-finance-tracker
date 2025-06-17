document.addEventListener('DOMContentLoaded', function() {
    const dateRangeField = document.getElementById('id_date_range');
    const startDateField = document.getElementById('id_start_date');
    const endDateField = document.getElementById('id_end_date');

    if (!dateRangeField || !startDateField || !endDateField) {
        return; // Fields not found, exit gracefully
    }

    function updateDateFields() {
        const selectedRange = dateRangeField.value;
        
        if (selectedRange === 'custom') {
            startDateField.disabled = false;
            endDateField.disabled = false;
            startDateField.required = true;
            endDateField.required = true;
        } else {
            startDateField.disabled = true;
            endDateField.disabled = true;
            startDateField.required = false;
            endDateField.required = false;
            
            // Auto-calculate dates based on selection
            const today = new Date();
            let startDate, endDate = today.toISOString().split('T')[0];
            
            switch (selectedRange) {
                case '30days':
                    startDate = new Date(today.getTime() - (30 * 24 * 60 * 60 * 1000));
                    break;
                case '3months':
                    startDate = new Date(today.getTime() - (90 * 24 * 60 * 60 * 1000));
                    break;
                case '6months':
                    startDate = new Date(today.getTime() - (180 * 24 * 60 * 60 * 1000));
                    break;
                case '1year':
                    startDate = new Date(today.getTime() - (365 * 24 * 60 * 60 * 1000));
                    break;
                case 'ytd':
                    startDate = new Date(today.getFullYear(), 0, 1);
                    break;
                default:
                    startDate = new Date(today.getTime() - (90 * 24 * 60 * 60 * 1000));
            }
            
            if (startDate) {
                startDateField.value = startDate.toISOString().split('T')[0];
                endDateField.value = endDate;
            }
        }
    }

    // Initialize on page load
    updateDateFields();

    // Update when selection changes
    dateRangeField.addEventListener('change', updateDateFields);
});