document.addEventListener('DOMContentLoaded', function () {
    const accountsData = JSON.parse(document.getElementById('accounts-data').textContent);
    const categoriesData = JSON.parse(document.getElementById('categories-data').textContent);
    const transactionTypesData = JSON.parse(document.getElementById('transaction-types-data').textContent);
    const initialSpreadsheetData = JSON.parse(document.getElementById('initial-spreadsheet-data').textContent);

    
    const container = document.getElementById('transaction-spreadsheet');
    const saveButton = document.getElementById('save-spreadsheet-btn');
    const addRowButton = document.getElementById('add-row-btn');
    const statusMessageEl = document.getElementById('status-message');

    const modifiedRowIndexes = new Set(); 


    // Prepare sources for dropdowns
    const accountNames = accountsData.map(acc => `${acc.account_type} (${acc.account_number})`);
    const categoryNames = categoriesData.map(cat => cat.name);
    const transactionTypeNames = transactionTypesData.map(tt => tt.name);

    const hot = new Handsontable(container, {
        data: initialSpreadsheetData.length > 0 ? initialSpreadsheetData : [{}],
        rowHeaders: true,
        colHeaders: ['ID', 'Date', 'Account', 'Category', 'Description', 'Amount', 'Type'],
        columns: [
            { data: 'id', readOnly: true, type: 'numeric', width: 50 }, // Transaction ID column, read only
            { data: 'date', type: 'date', dateFormat: 'YYYY-MM-DD', correctFormat: true, allowInvalid: false },
            {
                data: 'account_name',
                type: 'dropdown', 
                source: accountNames,
                allowInvalid: false,
                validator: function (value, callback) {
                    // Allow empty for new rows or if account is not set
                    if (value === null || value === '' || accountNames.includes(value)) {
                        callback(true);
                    } else {
                        callback(false);
                    }
                }
            },
            { 
                data: 'category_name',
                type: 'dropdown', 
                source: categoryNames,
                allowInvalid: false,
                validator: function (value, callback) {
                     // Allow empty for new rows or if category is not set
                    if (value === null || value === '' || categoryNames.includes(value)) {
                        callback(true);
                    } else {
                        callback(false);
                    }
                }
            },
            { data: 'description', type: 'text' },
            { data: 'amount', type: 'numeric', numericFormat: { pattern: '0,0.00' }, allowInvalid: false },
            { 
                data: 'transaction_type_name',
                type: 'dropdown', 
                source: transactionTypeNames,
                allowInvalid: false,
                validator: function (value, callback) {
                    if (value === null || value === '' || transactionTypeNames.includes(value)) {
                        callback(true);
                    } else {
                        callback(false);
                    }
                }
            }
        ],
        // to hide the id column:
        // hiddenColumns: {
        //  columns: [0], // Index of the ID column
        //  indicators: false // Do not show hidden column indicators
        // },
        minRows: 50, 
        minSpareRows: 10, 
        width: '100%',
        height: '100%', 
        stretchH: 'all',
        licenseKey: 'non-commercial-and-evaluation',
        
        // Enhanced features
        manualRowMove: true,
        manualColumnMove: true,
        manualRowResize: true,
        manualColumnResize: true,
        undoRedo: true,
        
        // Context menu and interaction
        contextMenu: ['row_above', 'row_below', 'remove_row', '---------', 'col_left', 'col_right', 'remove_col'],
        filters: true,
        dropdownMenu: ['filter_by_condition', 'filter_operators', 'filter_by_condition2', 'filter_by_value', 'filter_action_bar'],
        
        // Selection and navigation
        fillHandle: true,
        autoWrapRow: true,
        autoWrapCol: true,
        
        // Grid appearance
        rowHeaders: true,
        // colHeaders: true,
        outsideClickDeselects: false,
        
        // Performance
        virtualization: true,
        
        afterChange: function (changes, source) {
            if (source === 'loadData' || !changes) {
                return; 
            }
            changes.forEach(([rowIndex, prop, oldValue, newValue]) => {
                if (String(oldValue) !== String(newValue)) {
                    modifiedRowIndexes.add(rowIndex);
                    updateStatus(`Modified row ${rowIndex + 1}`);
                }
            });
        },
        
        afterSelection: function(row, column, row2, column2, preventScrolling, selectionLayerLevel) {
            updateStatus(`Selected: R${row + 1}C${column + 1}`);
        }
    });

    function updateStatus(message) {
        const statusEl = document.getElementById('status-message');
        statusEl.textContent = message;
        setTimeout(() => {
            statusEl.textContent = 'Ready';
        }, 3000);
    }

    // keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 's':
                    e.preventDefault();
                    document.getElementById('save-spreadsheet-btn').click();
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

    const undoRedoPlugin = hot.getPlugin('undoRedo');
    // undo/redo button functionality (fix hot undo/redo with plugin since depreciated)
    document.getElementById('undo-btn').addEventListener('click', () => {
        undoRedoPlugin.undo();
    });

    document.getElementById('redo-btn').addEventListener('click', () => {
        undoRedoPlugin.redo();
    });

    addRowButton.addEventListener('click', function() {
        hot.alter('insert_row_below');
    });

    saveButton.addEventListener('click', function () {
    const tableData = hot.getSourceData();
    const transactionsToSave = [];
    statusMessageEl.innerHTML = '<span class="text-info">Saving...</span>';

    tableData.forEach((row, rowIndex) => {
        const isNew = !row.id && row.date && row.amount != null;
        const isModified = row.id && modifiedRowIndexes.has(rowIndex);
        if (isNew || isModified) {
            // Parse "checking (00010)" format
            const accountMatch = row.account_name.match(/^(.+?)\s*\((.+?)\)$/);
            if (accountMatch) {
                const accountNumber = accountMatch[2];
                account = accountsData.find(acc => acc.account_number === accountNumber);
            }
            const category = categoriesData.find(cat => cat.name === row.category_name);
            const transactionType = transactionTypesData.find(tt => tt.name === row.transaction_type_name);

            transactionsToSave.push({
                id: row.id || null,
                date: row.date,
                account_id: account ? account.id : null,
                category_id: category ? category.id : null,
                description: row.description || '',
                amount: row.amount,
                transaction_type: transactionType ? transactionType.id : (row.transaction_type_name ? row.transaction_type_name.toLowerCase() : 'expense'),
                rowIndex: rowIndex // Add row index to track which row this is
            });
        }
    });

    if (transactionsToSave.length === 0) {
        statusMessageEl.innerHTML = '<span class="text-warning">No new or modified transactions to save.</span>';
        return;
    }

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(window.saveSpreadsheetUrl, {
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
            
            // Update the spreadsheet data with new IDs for created transactions
            if (data.created_transactions) {
                data.created_transactions.forEach(newTransaction => {
                    // Find the row that was saved and update it with the new ID
                    const savedTransaction = transactionsToSave.find(t => 
                        t.rowIndex !== undefined && 
                        t.date === newTransaction.date && 
                        parseFloat(t.amount) === parseFloat(newTransaction.amount) &&
                        t.description === newTransaction.description
                    );
                    
                    if (savedTransaction) {
                        // Update the cell data in Handsontable
                        hot.setDataAtCell(savedTransaction.rowIndex, 0, newTransaction.id, 'loadData');
                    }
                });
            }
            
            // Clear modified row tracking
            modifiedRowIndexes.clear();
            
            // Show success message temporarily
            setTimeout(() => {
                statusMessageEl.textContent = 'Ready';
            }, 3000);
            
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
});