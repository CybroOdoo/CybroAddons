import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { PrintPopup } from "@simplified_pos/js/PrintPopup";

export class ConfirmationPopup extends Component {
    static template = "simplified_pos.ConfirmationPopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        confirmText: { type: String, optional: true },
        cancelText: { type: String, optional: true },
        bodyText: { type: String, optional: true },
        close: { type: Function, optional: true },
        getPayload: { type: Function, optional: true },
        id: { type: String, optional: true },
    };
    setup() {
        super.setup();
        this.pos = usePos();
        this.dialog = useService("dialog");
    }
    async finalizeOrder(order) {
        if (!order) return;
        if (order.state !== "paid") {
            order.state = "paid";
            if (typeof this.pos.addPendingOrder === "function") {
                this.pos.addPendingOrder([order.id]);
            }
            try {
                if (this.pos.data?.localUnsyncedPaidOrderUuids) {
                    const unsyncedSet = typeof this.pos.data.localUnsyncedPaidOrderUuids === "function"
                        ? this.pos.data.localUnsyncedPaidOrderUuids()
                        : this.pos.data.localUnsyncedPaidOrderUuids;
                    if (unsyncedSet && typeof unsyncedSet.add === "function") {
                        unsyncedSet.add(order.uuid);
                    }
                }
            } catch (e) {
                // Ignore if method not present
            }
            try {
                if (typeof this.pos.syncAllOrders === "function") {
                    await this.pos.syncAllOrders({ throw: false });
                }
            } catch (e) {
                // Ignore sync error if offline or not supported
            }
        }
    }
    async confirm(ev) {
        const order = typeof this.pos.getOrder === "function" ? this.pos.getOrder() : this.pos.currentOrder;
        if (order) {
            await this.finalizeOrder(order);
        }
        if (this.props.close) {
            this.props.close();
        }
        this.dialog.add(PrintPopup, {
            title: _t('Print order'),
            confirmText: _t('Print'),
            cancelText: _t('Cancel'),
            orderToPrint: order,
        });
    }
    async getPayload() {
        return null;
    }
    cancel(ev) {
        if (this.props.close) {
            this.props.close();
        }
    }
}
