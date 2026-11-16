/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(GeneratePrinterData.prototype, {
    generateReceiptData() {
        const data = super.generateReceiptData(...arguments);
        const order = this.order;
        if (order) {
            const bookedData = order.booked_data || order.uiState?.booked_data;
            const isBooked = order.is_booked || order.uiState?.is_booked;
            const bookingRef = order.booking_ref_id || order.uiState?.booking_ref_id;
            if (bookedData || isBooked || bookingRef) {
                const b = bookedData || {};
                const name =
                    b.name ||
                    order.booking_ref_name ||
                    order.uiState?.booking_ref_name ||
                    (typeof bookingRef === "object"
                        ? (bookingRef.name || bookingRef[1])
                        : typeof bookingRef === "string"
                        ? bookingRef
                        : false);
                data.extra_data.booking_info = {
                    name: name || false,
                    phone: b.phone || false,
                    note: b.note || false,
                    pickup: b.pickup || false,
                    deliver: b.deliver || false,
                    address: b.address || false,
                };
            }
        }
        return data;
    },
});

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(vals);
        if (vals) {
            if (vals.booking_ref_id) this.booking_ref_id = vals.booking_ref_id;
            if (vals.booking_ref_name) this.booking_ref_name = vals.booking_ref_name;
            if (vals.is_booked) this.is_booked = vals.is_booked;
            if (vals.booked_data) this.booked_data = vals.booked_data;
        }
    },
    serializeForORM(opts = {}) {
        const res = super.serializeForORM(opts);
        const bookedId =
            this.booking_ref_id ||
            this.uiState?.booking_ref_id ||
            (this.booked_data && this.booked_data.id) ||
            (this.uiState?.booked_data && this.uiState.booked_data.id);
        if (bookedId) {
            res.booking_ref_id = typeof bookedId === "object" ? bookedId.id : bookedId;
        }
        return res;
    },
});
