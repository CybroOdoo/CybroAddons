/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { ProxyStatus } from "@point_of_sale/app/navbar/proxy_status/proxy_status";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { SaleDetailsButton } from "@point_of_sale/app/navbar/sale_details_button/sale_details_button";
import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { BackButton } from "@point_of_sale/app/screens/product_screen/action_pad/back_button/back_button";
import { CashierName } from "@point_of_sale/app/navbar/cashier_name/cashier_name";
import { OrderTabs } from "@point_of_sale/app/components/order_tabs/order_tabs";

ProductScreen.components = {
    ...ProductScreen.components,
    ProxyStatus,
    SaleDetailsButton,
    BackButton,
    CashierName,
    OrderTabs,
}

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.hardwareProxy = useService("hardware_proxy");
        this.selectedCategoryId = null;
    },
    setSelectedCategory(categoryId) {
        this.selectedCategoryId = categoryId;
        this.pos.setSelectedCategory(categoryId);
        this.render();  // manually trigger re-render
    },
     async closeSession() {
        const info = await this.pos.getClosePosInfo();
        this.dialog.add(ClosePosPopup, info);
    },
    onCashMoveButtonClick() {
        this.hardwareProxy.openCashbox(_t("Cash in / out"));
        this.dialog.add(CashMovePopup);
    },
    get orderCount() {
        return this.pos.get_open_orders().length;
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


patch(ProductScreen.prototype,{

    getOrderTabs() {
        return this.pos.get_open_orders().filter((order) => !order.table_id);
    },

});