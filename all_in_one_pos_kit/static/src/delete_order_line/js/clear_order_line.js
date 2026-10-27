/** @odoo-module */

window.posDeleteOrderLine = function(lineId, posInstance) {
    const order = posInstance.selectedOrder;

    if (order) {
        const lines = order.lines;
        const lineToRemove = lines.find(line => line.id === lineId);

        if (lineToRemove) {
            order.removeOrderline(lineToRemove);
        }
    }
};

