/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { WarningDialog} from "@web/core/errors/error_dialogs";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

class CsCartConnector extends Component {
    setup() {
        this.orm = useService("orm");
        this.dialogService = useService("dialog");
        this.notificationService = useService("notification");
    }

    async importOrders() {
        try{
            const result = await this.orm.call(
                "cs.cart.order.sync",
                "sync_orders",
                []
            );
            if (result && result.success) {
                this.dialogService.add(ConfirmationDialog, {
                    title: _t("Order Sync"),
                    body: _t("Successfully imported the orders"),
                    confirm: () => {
                       this.notificationService.add(_t("Action completed successfully"), {
                           type: "success",
                       });
                    }
                });
            }
            if (result?.reason === "missing_products") {
                this.dialogService.add(WarningDialog, {
                    title: _t("Products Missing"),
                    message: _t(
                        "Please import products from CS-Cart and try again."
                    ),
                });
            }

        }catch (error) {
            this.notificationService.add(
                    `Order import blocked`,
                    {
                        type: "error",
                    }
                );
            console.error(error);
        }

    }

    async importProducts() {
        try{
            const result = await this.orm.call("cs.cart.product.sync", "sync_products", []);
            if (result && result.success) {
                this.dialogService.add(ConfirmationDialog, {
                    title: _t("Product Sync"),
                    body: _t("Successfully imported the Products"),
                    confirm: () => {
                       this.notificationService.add(_t("Action completed successfully"), {
                           type: "success",
                       });
                    }
                });
            }
        }catch (error) {
            this.notificationService.add(
                    `Product import blocked`,
                    {
                        type: "error",
                    }
                );
            console.error(error);
        }

    }

    async importCustomers() {
        try {
            const result = await this.orm.call(
                "cs.cart.customer.sync",
                "sync_customers",
                []
            );

            if (result && result.success) {
                this.dialogService.add(ConfirmationDialog, {
                    title: _t("Customer Sync"),
                    body: _t("Successfully imported the Customer"),
                    confirm: () => {
                       this.notificationService.add(_t("Action completed successfully"), {
                           type: "success",
                       });
                    }
                });
            }
        } catch (error) {
            this.notificationService.add(
                    `Customer import blocked`,
                    {
                        type: "error",
                    }
                );
            console.error(error);
        }
    }

    async importVendors() {
        try{
            const result = await this.orm.call("cs.cart.vendor.sync", "sync_vendors", []);
            if (result && result.success) {
                this.dialogService.add(ConfirmationDialog, {
                    title: _t("Vendor Sync"),
                    body: _t("Successfully imported the Vendors"),
                    confirm: () => {
                       this.notificationService.add(_t("Action completed successfully"), {
                           type: "success",
                       });
                    }
                });
            }
        } catch (error) {
            this.notificationService.add(
                    `Vendor import blocked`,
                    {
                        type: "error",
                    }
                );
            console.error(error);
        }
    }

}

CsCartConnector.template = "odoo_cscart_connector.CsCartConnector";

registry.category("actions").add("cs_cart_connector", CsCartConnector);


const csCartImportBatchReloadService = {
    dependencies: ["bus_service", "action", "notification"],
    start(env, { bus_service, action, notification }) {
        bus_service.subscribe("cs_cart_import_batch_reload", (payload) => {
            const controller = action.currentController;
            if (controller) {
                const resModel = controller.props?.resModel || controller.action?.res_model;
                if (resModel === "cs.cart.import.batch" || resModel === "cs.cart.config") {
                    action.doAction("soft_reload");
                }
            }
            if (payload && payload.state) {
                if (payload.state === "done") {
                    notification.add(
                        _t(`Import batch "${payload.name}" has completed successfully.`),
                        {
                            title: _t("Import Completed"),
                            type: "success",
                            sticky: false,
                        }
                    );
                } else if (payload.state === "failed") {
                    notification.add(
                        _t(`Import batch "${payload.name}" has failed. Please check the logs.`),
                        {
                            title: _t("Import Failed"),
                            type: "danger",
                            sticky: true,
                        }
                    );
                }
            }
        });
    }
};

registry.category("services").add("cs_cart_import_batch_reload", csCartImportBatchReloadService);

