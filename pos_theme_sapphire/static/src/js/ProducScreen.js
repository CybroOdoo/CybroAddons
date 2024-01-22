/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

import { patch } from "@web/core/utils/patch";
import { ProxyStatus } from "@point_of_sale/app/navbar/proxy_status/proxy_status";
import { SyncNotification } from "@point_of_sale/app/navbar/sync_notification/sync_notification";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { SaleDetailsButton } from "@point_of_sale/app/navbar/sale_details_button/sale_details_button";
import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { BackButton } from "@point_of_sale/app/navbar/back_button/back_button";

ProductScreen.components = {
    ...ProductScreen.components,
    ProxyStatus,
    SyncNotification,
    SaleDetailsButton,
    BackButton,
}
patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.hardwareProxy = useService("hardware_proxy");
    },
     async closeSession() {
        const info = await this.pos.getClosePosInfo();
        this.popup.add(ClosePosPopup, { ...info, keepBehind: true });
    },
    onCashMoveButtonClick() {
        this.hardwareProxy.openCashbox(_t("Cash in / out"));
        this.popup.add(CashMovePopup);
    },
    get orderCount() {
        return this.pos.get_order_list().length;
    },
    async onTicketButtonClick() {
        if (this.isTicketScreenShown) {
            this.pos.closeScreen();
        } else {
            if (this._shouldLoadOrders()) {
                try {
                    this.pos.setLoadingOrderState(true);
                    const message = await this.pos._syncAllOrdersFromServer();
                    if (message) {
                        this.notification.add(message, 5000);
                    }
                } finally {
                    this.pos.setLoadingOrderState(false);
                    this.pos.showScreen("TicketScreen");
                }
            } else {
                this.pos.showScreen("TicketScreen");
            }
        }
    },

    _shouldLoadOrders() {
        return this.pos.config.trusted_config_ids.length > 0;
    },
    showBackButton() {
        return this.pos.showBackButton() && this.ui.isSmall;
    },
});
