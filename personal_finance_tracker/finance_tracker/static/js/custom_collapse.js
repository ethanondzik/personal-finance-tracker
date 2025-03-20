
/**
 * Toggles the visibility of a collapsible row in the transactions table.
 *
 * This function is triggered when a user clicks on a transaction row.
 * It identifies the corresponding details row (using the transaction ID)
 * and toggles the 'show' class to either display or hide the row.
 *
 * @param {string} transactionId - The unique ID of the transaction.
 *                                 This ID is used to locate the corresponding
 *                                 details row in the table.
 *
 * Behavior:
 * - If the details row is currently hidden (does not have the 'show' class),
 *   the function adds the 'show' class to make it visible.
 * - If the details row is currently visible (has the 'show' class),
 *   the function removes the 'show' class to hide it.
 *
 * Prerequisites:
 * - The details row must have an ID in the format `details<transactionId>`.
 * - The 'show' class should be defined in the CSS to control visibility.
 *
 * Example:
 * - For a transaction with ID '123', the details row should have an ID of 'details123'.
 * - Clicking on the transaction row will call toggleDetails('123'),
 *   which will toggle the visibility of the row with ID 'details123'.
 *
 * Usage:
 * - Attach this function to the `onclick` event of a transaction row in the HTML.
 */
function toggleDetails(transactionId) {
    const detailsRow = document.getElementById(`details${transactionId}`);
    if (detailsRow) {
        detailsRow.classList.toggle('show'); // Toggle the 'show' class
    }
}
