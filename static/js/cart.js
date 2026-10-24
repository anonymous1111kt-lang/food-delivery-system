// QuickBite Cart Interactivity and Utilities

function updateCartQty(itemId, change) {
    const qtyInput = document.getElementById(`qty-${itemId}`);
    if (!qtyInput) return;
    let currentQty = parseInt(qtyInput.value) || 1;
    let newQty = currentQty + change;
    if (newQty < 1) newQty = 1;
    qtyInput.value = newQty;
}

document.addEventListener('DOMContentLoaded', () => {
    // Enable Bootstrap tooltips if any
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
