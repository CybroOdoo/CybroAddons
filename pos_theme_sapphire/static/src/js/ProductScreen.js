/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ProxyStatus } from "@point_of_sale/app/components/navbar/proxy_status/proxy_status";
import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { SaleDetailsButton } from "@point_of_sale/app/components/navbar/sale_details_button/sale_details_button";
import { CashMovePopup } from "@point_of_sale/app/components/popups/cash_move_popup/cash_move_popup";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { BackButton } from "@point_of_sale/app/screens/product_screen/action_pad/back_button/back_button";
import { CashierName } from "@point_of_sale/app/components/navbar/cashier_name/cashier_name";
import { CategorySelector } from "@point_of_sale/app/components/category_selector/category_selector";
import { user } from "@web/core/user";
import { OrderTabs } from "@point_of_sale/app/components/order_tabs/order_tabs";

ProductScreen.components = {
    ...ProductScreen.components,
    ProxyStatus,
    SaleDetailsButton,
    BackButton,
    CashierName,
    CategorySelector,
    OrderTabs,
};

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.hardwareProxy = useService("hardware_proxy");
        this.onCategorySelected = this.onCategorySelected.bind(this);
    },

    onCategorySelected({ categoryId }) {
        this.pos.setSelectedCategory(categoryId);
        this.render(true);
    },

    setSelectedCategory(categoryId) {
        this.selectedCategoryId = categoryId;
        this.pos.setSelectedCategory(categoryId);
        this.render();
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
        return this.pos.getOrder().length;
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
                    this.pos.navigate("TicketScreen");
                }
            } else {
                this.pos.navigate("TicketScreen");
            }
        }
    },
    _shouldLoadOrders() {
        return this.pos.config.trusted_config_ids.length > 0;
    },
    showBackButton() {
        return this.ui?.isSmall && typeof this.pos.showBackButton === "function" && this.pos.showBackButton();
    }
});

patch(CashierName.prototype, {
    setup() {
        super.setup(...arguments);
        this.username = user.name
        this.email = user.email
    },
});

patch(ProductScreen.prototype, {
    getOrderTabs() {
        return this.pos.getOpenOrders().filter(o => !o.table_id);
    },
});
