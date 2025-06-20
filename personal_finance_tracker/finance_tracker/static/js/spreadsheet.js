document.addEventListener('DOMContentLoaded', function () {
    // Fetch spreadsheet data via AJAX
    fetch('/api/spreadsheet/data/', {
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        window.accountsData = data.accounts || [];
        window.categoriesData = data.categories || [];
        window.transactionTypesData = data.transaction_types || [];
        window.initialSpreadsheetData = data.transactions || [];
        initializeHandsontable();
    })
    .catch(error => {
        console.error('Error fetching spreadsheet data:', error);
        document.getElementById('status-message').innerHTML = '<span class="text-danger">Failed to load spreadsheet data. Check console for details.</span>';
    });

    // Handsontable and UI setup
    function initializeHandsontable() {
        const container = document.getElementById('transaction-spreadsheet');
        const saveButton = document.getElementById('save-spreadsheet-btn');
        const addRowButton = document.getElementById('add-row-btn');
        const deleteRowButton = document.getElementById('delete-row-btn');
        const deleteModal = document.getElementById('deleteModal');
        const deleteModalBody = deleteModal.querySelector('.modal-body');
        const confirmDeleteBtn = document.getElementById('confirm-spreadsheet-delete-btn');
        const statusMessageEl = document.getElementById('status-message');
        const modifiedRowIndexes = new Set();

        // Prepare dropdown sources
        const accountNames = window.accountsData.map(acc => `${acc.account_type} (${acc.account_number})`);
        const categoryNames = window.categoriesData.map(cat => cat.name);
        const transactionTypeNames = window.transactionTypesData.map(tt => tt.name);

        // Initialize Handsontable
        const hot = new Handsontable(container, {
            data: window.initialSpreadsheetData.length > 0 ? window.initialSpreadsheetData : [{}],
            rowHeaders: true,
            colHeaders: ['ID', 'Date', 'Account', 'Category', 'Description', 'Amount', 'Type'],
            columns: [
                { data: 'id', readOnly: true, type: 'numeric', width: 50 },
                { data: 'date', type: 'date', dateFormat: 'YYYY-MM-DD', correctFormat: true, allowInvalid: false },
                {
                    data: 'account_name',
                    type: 'dropdown',
                    source: accountNames,
                    allowInvalid: false,
                    validator: (value, callback) => callback(value === null || value === '' || accountNames.includes(value))
                },
                {
                    data: 'category_name',
                    type: 'dropdown',
                    source: categoryNames,
                    allowInvalid: false,
                    validator: (value, callback) => callback(value === null || value === '' || categoryNames.includes(value))
                },
                { data: 'description', type: 'text' },
                { data: 'amount', type: 'numeric', numericFormat: { pattern: '0,0.00' }, allowInvalid: false },
                {
                    data: 'transaction_type_name',
                    type: 'dropdown',
                    source: transactionTypeNames,
                    allowInvalid: false,
                    validator: (value, callback) => callback(value === null || value === '' || transactionTypeNames.includes(value))
                }
            ],
            minRows: 50,
            minSpareRows: 10,
            width: '100%',
            height: '100%',
            stretchH: 'all',
            licenseKey: 'non-commercial-and-evaluation',
            manualRowMove: true,
            manualColumnMove: true,
            manualRowResize: true,
            manualColumnResize: true,
            undoRedo: true,
            contextMenu: ['row_above', 'row_below', 'remove_row', '---------', 'col_left', 'col_right', 'remove_col'],
            filters: true,
            dropdownMenu: ['filter_by_condition', 'filter_operators', 'filter_by_condition2', 'filter_by_value', 'filter_action_bar'],
            fillHandle: true,
            autoWrapRow: true,
            autoWrapCol: true,
            virtualization: true,
            afterChange: function (changes, source) {
                if (source === 'loadData' || !changes) return;
                changes.forEach(([rowIndex, prop, oldValue, newValue]) => {
                    if (String(oldValue) !== String(newValue)) {
                        modifiedRowIndexes.add(rowIndex);
                        updateStatus(`Modified row ${rowIndex + 1}`);
                    }
                });
            },
            afterSelection: function(row, column) {
                updateStatus(`Selected: R${row + 1}C${column + 1}`);
            },
            afterSelectionEnd: function(row, col, row2, col2) {
                lastSelected = [row, col, row2, col2];
            }
        });

        function updateStatus(message) {
            statusMessageEl.textContent = message;
            setTimeout(() => { statusMessageEl.textContent = 'Ready'; }, 5000);
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 's':
                        e.preventDefault();
                        saveButton.click();
                        break;
                    case 'z':
                        if (!e.shiftKey) {
                            e.preventDefault();
                            hot.undo();
                        }
                        break;
                    case 'y':
                        e.preventDefault();
                        hot.redo();
                        break;
                }
            }
        });

        // Undo/Redo buttons
        const undoRedoPlugin = hot.getPlugin('undoRedo');
        document.getElementById('undo-btn').addEventListener('click', () => undoRedoPlugin.undo());
        document.getElementById('redo-btn').addEventListener('click', () => undoRedoPlugin.redo());

        // Add row
        addRowButton.addEventListener('click', () => hot.alter('insert_row_below'));

        // Save
        saveButton.addEventListener('click', function () {
            const tableData = hot.getSourceData();
            const transactionsToSave = [];
            statusMessageEl.innerHTML = '<span class="text-info">Saving...</span>';

            tableData.forEach((row, rowIndex) => {
                const isNew = !row.id && row.date && row.amount != null;
                const isModified = row.id && modifiedRowIndexes.has(rowIndex);
                if (isNew || isModified) {
                    let account = null;
                    const accountMatch = row.account_name && row.account_name.match(/^(.+?)\s*\((.+?)\)$/);
                    if (accountMatch) {
                        const accountNumber = accountMatch[2];
                        account = window.accountsData.find(acc => acc.account_number === accountNumber);
                    }
                    const category = window.categoriesData.find(cat => cat.name === row.category_name);
                    const transactionType = window.transactionTypesData.find(tt => tt.name === row.transaction_type_name);

                    transactionsToSave.push({
                        id: row.id || null,
                        date: row.date,
                        account_id: account ? account.id : null,
                        category_id: category ? category.id : null,
                        description: row.description || '',
                        amount: row.amount,
                        transaction_type: transactionType ? transactionType.id : (row.transaction_type_name ? row.transaction_type_name.toLowerCase() : 'expense'),
                        rowIndex: rowIndex
                    });
                }
            });

            if (transactionsToSave.length === 0) {
                statusMessageEl.innerHTML = '<span class="text-warning">No new or modified transactions to save.</span>';
                return;
            }

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            fetch('/api/spreadsheet/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(transactionsToSave)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusMessageEl.innerHTML = `<span class="text-success">${data.message}</span>`;
                    if (data.created_transactions) {
                        data.created_transactions.forEach(newTransaction => {
                            const savedTransaction = transactionsToSave.find(t =>
                                t.rowIndex !== undefined &&
                                t.date === newTransaction.date &&
                                parseFloat(t.amount) === parseFloat(newTransaction.amount) &&
                                t.description === newTransaction.description
                            );
                            if (savedTransaction) {
                                hot.setDataAtCell(savedTransaction.rowIndex, 0, newTransaction.id, 'loadData');
                            }
                        });
                    }
                    modifiedRowIndexes.clear();
                    setTimeout(() => { statusMessageEl.textContent = 'Ready'; }, 3000);
                } else {
                    let errorMessages = data.message || 'An error occurred.';
                    if (data.errors && data.errors.length > 0) {
                        errorMessages += '<ul>' + data.errors.map(err => `<li>${err}</li>`).join('') + '</ul>';
                    }
                    statusMessageEl.innerHTML = `<div class="alert alert-danger">${errorMessages}</div>`;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                statusMessageEl.innerHTML = '<span class="text-danger">An error occurred while saving. Check console.</span>';
            });
        });

        // Delete logic
        let idsPendingServerDeletion = [];
        deleteRowButton.addEventListener('click', function() {
            let selected = hot.getSelected();
            if ((!selected || selected.length === 0) && lastSelected) {
                selected = [lastSelected];
            }
            if (!selected || selected.length === 0) {
                updateStatus('No rows selected to delete.');
                return;
            }
            const rowsToRemoveLocally = new Set();
            const transactionsForServerDeletion = [];
            selected.forEach(sel => {
                const fromRow = Math.min(sel[0], sel[2]);
                const toRow = Math.max(sel[0], sel[2]);
                for (let rowIndex = fromRow; rowIndex <= toRow; rowIndex++) {
                    if (rowIndex < hot.countRows()) {
                        const rowData = hot.getSourceDataAtRow(rowIndex);
                        if (rowData && rowData.id) {
                            if (!transactionsForServerDeletion.some(t => t.id === rowData.id)) {
                                transactionsForServerDeletion.push({ id: rowData.id, visualIndex: rowIndex });
                            }
                        } else if (rowData && (rowData.date || rowData.description || rowData.amount !== undefined)) {
                            rowsToRemoveLocally.add(rowIndex);
                        }
                    }
                }
            });
            let localRowsRemovedCount = 0;
            if (rowsToRemoveLocally.size > 0) {
                const sortedLocalRows = Array.from(rowsToRemoveLocally).sort((a, b) => b - a);
                sortedLocalRows.forEach(rowIndex => {
                    hot.alter('remove_row', rowIndex, 1);
                    localRowsRemovedCount++;
                });
            }
            if (transactionsForServerDeletion.length > 0) {
                idsPendingServerDeletion = transactionsForServerDeletion.map(t => t.id);
                deleteModalBody.innerHTML = `Are you sure you want to delete ${idsPendingServerDeletion.length} selected transaction(s) from the database? This action cannot be undone.`;
                const modal = new bootstrap.Modal(deleteModal);
                modal.show();
            } else if (localRowsRemovedCount > 0) {
                updateStatus(`${localRowsRemovedCount} new row(s) removed.`);
                hot.render();
            } else {
                updateStatus('No rows with data selected to delete.');
            }
        });

        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', function() {
                if (idsPendingServerDeletion.length > 0) {
                    statusMessageEl.innerHTML = '<span class="text-info">Deleting...</span>';
                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    fetch('/api/spreadsheet/delete/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                        },
                        body: JSON.stringify({ transaction_ids: idsPendingServerDeletion })
                    })
                    .then(response => response.json())
                    .then(data => {
                        const modal = bootstrap.Modal.getInstance(deleteModal);
                        if (modal) modal.hide();
                        if (data.status === 'success') {
                            const successfullyDeletedIds = new Set(idsPendingServerDeletion);
                            const rowsToRemoveFromHot = [];
                            const currentData = hot.getSourceData();
                            for (let i = 0; i < currentData.length; i++) {
                                if (currentData[i] && successfullyDeletedIds.has(currentData[i].id)) {
                                    rowsToRemoveFromHot.push(i);
                                }
                            }
                            rowsToRemoveFromHot.sort((a, b) => b - a);
                            rowsToRemoveFromHot.forEach(visualIndex => {
                                hot.alter('remove_row', visualIndex, 1);
                            });
                            updateStatus(data.message || `${successfullyDeletedIds.size} transaction(s) deleted.`);
                            hot.render();
                        } else {
                            updateStatus(`Error: ${data.message || 'Failed to delete transactions.'}`);
                        }
                        idsPendingServerDeletion = [];
                    })
                    .catch(error => {
                        console.error('Error deleting transactions:', error);
                        const modal = bootstrap.Modal.getInstance(deleteModal);
                        if (modal) modal.hide();
                        updateStatus('An error occurred while deleting transactions.');
                        idsPendingServerDeletion = [];
                    });
                }
            });
        }
    }
});