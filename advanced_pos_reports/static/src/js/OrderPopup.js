/** @odoo-module **/
import { Component, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { OrderSummaryReceiptScreen } from "./OrderReceiptPopup";

export class OrderSummaryPopup extends Component {
    static components = { Dialog };
    static template = "advanced_pos_reports.OrderSummaryPopup";
    props = useProps();

    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = proxy({
            current_session: false,
            start_date: "",
            end_date: "",
            status: "",
        });
    }

    click_is_session() {}

    async confirm() {
        const isSession = this.state.current_session;
        const startDate = this.state.start_date || "";
        const endDate = this.state.end_date || "";
        const status = this.state.status;
        let domain = [];

        if (isSession) {
            const currentSessionId = this.pos.config.current_session_id?.id || this.pos.session?.id;
            if (currentSessionId) {
                domain.push(["session_id", "=", currentSessionId]);
            }
        } else {
            if (!startDate.trim() || !endDate.trim()) {
                return;
            }
            if (startDate > endDate) {
                await this.dialog.add(AlertDialog, {
                    title: _t("Error"),
                    body: _t("Start Date cannot be greater than End Date."),
                });
                return;
            }
            domain.push(
                ["date_order", ">=", startDate + " 00:00:00"],
                ["date_order", "<=", endDate + " 23:59:59"]
            );
        }

        if (status) {
            domain.push(["state", "=", status]);
        }

        const orderIds = await this.orm.search("pos.order", domain);
        if (!orderIds || !orderIds.length) {
            await this.dialog.add(AlertDialog, {
                title: _t("No Data"),
                body: _t("No Data Available."),
            });
            return;
        }

        const orders = await this.orm.call("pos.order", "get_order_summary", [orderIds]);
        if (orders && orders.length > 0) {
            await this.dialog.add(OrderSummaryReceiptScreen, {
                title: _t("Order Summary Receipt"),
                orders: orders,
                start_date: startDate,
                end_date: endDate,
                data: this.pos,
            });
        } else {
            await this.dialog.add(AlertDialog, {
                title: _t("No Data"),
                body: _t("No Data Available."),
            });
        }
    }
}
