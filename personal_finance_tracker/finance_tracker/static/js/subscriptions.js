async function updateSubscriptionsCard() {
    try {
        const response = await fetch('/api/subscriptions/');
        const result = await response.json();
        if (result.status === 'success') {
            const subs = result.data;
            // Update summary
            const subsCount = document.getElementById('subscriptions-count');
            const subsNextDue = document.getElementById('subscriptions-next-due');
            if (subsCount) subsCount.textContent = `${subs.total} active`;
            if (subsNextDue) {
                if (subs.next_due_date && subs.next_due_name) {
                    const date = new Date(subs.next_due_date);
                    subsNextDue.textContent = `Next: ${subs.next_due_name} (${date.toLocaleDateString()})`;
                } else {
                    subsNextDue.textContent = 'No upcoming payments';
                }
            }
            // Update list
            const subsList = document.getElementById('subscriptions-list');
            if (subsList) {
                if (subs.preview && subs.preview.length > 0) {
                    subsList.innerHTML = subs.preview.map(sub =>
                        `<li class="subscription-item d-flex justify-content-between align-items-center py-2 border-bottom">
                            <div>
                                <span class="fw-semibold">${sub.name}</span>
                                <span class="text-muted ms-2">${sub.next_payment_date ? '(' + new Date(sub.next_payment_date).toLocaleDateString() + ')' : ''}</span>
                            </div>
                            <span class="text-muted">${sub.amount ? '$' + Number(sub.amount).toFixed(2) : ''}</span>
                        </li>`
                    ).join('');
                } else {
                    subsList.innerHTML = '<li class="text-muted">No active subscriptions</li>';
                }
            }
        }
    } catch (error) {
        console.error('Failed to update subscriptions card', error);
    }
}
document.addEventListener('DOMContentLoaded', updateSubscriptionsCard);