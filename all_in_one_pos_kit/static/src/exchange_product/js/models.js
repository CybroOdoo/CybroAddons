/** @odoo-module */
// In Odoo 18, pos.order data is loaded via _load_pos_data pattern.
// No need for _processData patch. Orders and lines are accessed
// through this.pos.models['pos.order'] and this.pos.models['pos.order.line'].
