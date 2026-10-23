import { Component, onWillStart, proxy } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class ImportDashBoard extends Component {
    static template = "import_dashboard.ImportDashBoard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        // Reactive state: the template re-renders when it changes
        this.state = proxy({
            permissions: {
                bill_of_material: false,
                pos: false,
                import_attendance: false,
                import_payment: false,
                import_task: false,
                import_sale: false,
                import_purchase: false,
                import_product_template: false,
                import_partner: false,
                import_invoice: false,
                import_pricelist: false,
                import_vendor_pricelist: false,
            },
            hasAnyPermission: false,
        });

        onWillStart(async () => {
            const result = await this.orm.call("ir.config_parameter", "check_user_group", []);
            Object.assign(this.state.permissions, result);
            this.state.hasAnyPermission = Object.values(result).some((v) => v);
        });
    }

    /**
     * Open an import wizard in a dialog.
     * @param {string} resModel technical name of the wizard model
     * @param {string} name dialog title
     */
    _openWizard(resModel, name) {
        this.action.doAction({
            name,
            type: "ir.actions.act_window",
            res_model: resModel,
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_sale() {
        this._openWizard("import.sale.order", _t("Import Sale Order"));
    }

    import_purchase() {
        this._openWizard("import.purchase.order", _t("Import Purchase Order"));
    }

    import_invoice() {
        this._openWizard("import.invoice", _t("Import Invoice"));
    }

    import_partner() {
        this._openWizard("import.partner", _t("Import Partner"));
    }

    import_product_pricelist() {
        this._openWizard("import.product.pricelist", _t("Import Product Pricelist"));
    }

    import_bill_of_material() {
        this._openWizard("import.bill.of.material", _t("Import Bills of Materials"));
    }

    import_product_template() {
        this._openWizard("import.product.template", _t("Import Product"));
    }

    import_vendor_pricelist() {
        this._openWizard("import.vendor.pricelist", _t("Import Vendor Pricelist"));
    }

    import_pos() {
        this._openWizard("import.pos.order", _t("Import POS Order"));
    }

    import_attendance() {
        this._openWizard("import.attendance", _t("Import Attendance"));
    }

    import_payment() {
        this._openWizard("import.payment", _t("Import Payment"));
    }

    import_task() {
        this._openWizard("import.task", _t("Import Task"));
    }
}

registry.category("actions").add("import_dashboard_tag", ImportDashBoard);
