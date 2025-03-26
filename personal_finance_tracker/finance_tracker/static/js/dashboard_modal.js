// Handle "Select All" functionality
document.addEventListener('DOMContentLoaded', function() {
    // Make sure select-all element exists before adding event listener
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.transaction-checkbox');
            checkboxes.forEach(checkbox => checkbox.checked = this.checked);
        });
    }

    // Set up event listener for the confirm-delete button
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            document.getElementById('delete-form').submit();
        });
    }

    // Add event listeners for cancel button
    const cancelBtn = document.querySelector('.modal-footer .btn-secondary');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            $('#deleteModal').modal('hide');
        });
    }

    const closeBtn = document.querySelector('.modal-header .close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            $('#deleteModal').modal('hide');
        });
    }
});

// Prepare modal for deleting a single transaction
function prepareDeleteSingle(id, description, amount, date) {
    // Uncheck all checkboxes first
    document.querySelectorAll('.transaction-checkbox').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Check only the specific transaction checkbox
    document.querySelector(`.transaction-checkbox[value="${id}"]`).checked = true;
    
    // Prepare and show the modal
    const transactionList = document.getElementById('transaction-list');
    transactionList.innerHTML = `<li class="list-group-item"><strong>${description}</strong> - ${amount} (${date})</li>`;
    
    $('#deleteModal').modal('show');
}

// Prepare modal for deleting multiple transactions
function prepareDeleteMultiple() {
    const selectedCheckboxes = document.querySelectorAll('.transaction-checkbox:checked');
    
    if (selectedCheckboxes.length === 0) {
        alert('Please select at least one transaction to delete.');
        return;
    }
    
    // Get details for all selected transactions
    const transactionList = document.getElementById('transaction-list');
    transactionList.innerHTML = '';
    
    selectedCheckboxes.forEach(checkbox => {
        const row = checkbox.closest('tr');
        const description = row.cells[4].textContent.trim();
        const amount = row.cells[3].textContent.trim();
        const date = row.cells[1].textContent.trim();
        
        transactionList.innerHTML += `<li class="list-group-item"><strong>${description}</strong> - ${amount} (${date})</li>`;
    });
    
    $('#deleteModal').modal('show');
}

// Toggle transaction details
function toggleDetails(transactionId) {
    const detailsRow = document.getElementById(`details${transactionId}`);
    if (detailsRow) {
        if (detailsRow.classList.contains('collapse')) {
            detailsRow.classList.remove('collapse');
        } else {
            detailsRow.classList.add('collapse');
        }
    }
}