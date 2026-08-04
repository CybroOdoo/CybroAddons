/** @odoo-module **/

import { Component, onWillStart, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");

export class ImportDashBoard extends Component {
    static template = "import_dashboard.ImportDashBoard";
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        // Reactive state - will trigger template re-render automatically
        this.state = useState({
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
            hasAnyPermission: false
        });

        onWillStart(async () => {
            try {
                const result = await this.orm.call("ir.config_parameter", "check_user_group", []);

                // Update permissions
                Object.assign(this.state.permissions, result);
                this.state.hasAnyPermission = Object.values(result).some(v => v);

            } catch (error) {
                console.error("Failed to load import permissions:", error);
            }
        });
        onMounted(() => {
            this._applyVisibility(); // Only kept for backward compatibility with your current template
        });
    }

    // Keep your DOM-based show/hide (temporary bridge)
    _applyVisibility() {
        // Applies visibility to dashboard cards based on user permissions.
        const root = this.el;
        if (!root) return;

        const set = (id, show) => {
            const el = root.querySelector(id);
            if (el) el.style.display = show ? "block" : "none";
        };
        const msg = root.querySelector(".start_msg");
        if (msg) msg.style.display = this.state.hasAnyPermission ? "none" : "block";

        set("#card_sale", this.state.permissions.import_sale);
        set("#card_purchase", this.state.permissions.import_purchase);
        set("#card_invoice", this.state.permissions.import_invoice);
        set("#card_partner", this.state.permissions.import_partner);
        set("#card_pricelist", this.state.permissions.import_pricelist);
        set("#card_vendor_pricelist", this.state.permissions.import_vendor_pricelist);
        set("#card_pos", this.state.permissions.pos);
        set("#card_attendance", this.state.permissions.import_attendance);
        set("#card_payment", this.state.permissions.import_payment);
        set("#card_task", this.state.permissions.import_task);
        set("#card_product", this.state.permissions.import_product_template);
        set("#card_bill_of_material", this.state.permissions.bill_of_material);
    }

    import_sale() {
    // Opens the wizard for importing Sale Orders.
        this.action.doAction({
            name: "Import Sale Order",
            type: "ir.actions.act_window",
            res_model: "import.sale.order",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_purchase() {
    // Opens the wizard for importing Purchase Orders.
        this.action.doAction({
            name: "Import Purchase Order",
            type: "ir.actions.act_window",
            res_model: "import.purchase.order",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_invoice() {
    // Opens the wizard for importing Invoices.
        this.action.doAction({
            name: "Import Invoice",
            type: "ir.actions.act_window",
            res_model: "import.invoice",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_partner() {
    // Opens the wizard for importing Partners.
        this.action.doAction({
            name: "Import Partner",
            type: "ir.actions.act_window",
            res_model: "import.partner",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_product_pricelist() {
    // Opens the wizard for importing Product Pricelists.
        this.action.doAction({
            name: "Import Product Pricelist",
            type: "ir.actions.act_window",
            res_model: "import.product.pricelist",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_bill_of_material() {
    // Opens the wizard for importing Bills of Material.
        this.action.doAction({
            name: "Import Bill of Material",
            type: "ir.actions.act_window",
            res_model: "import.bill.of.material",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_product_template() {
    // Opens the wizard for importing Product Templates.
        this.action.doAction({
            name: "Import Product",
            type: "ir.actions.act_window",
            res_model: "import.product.template",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_vendor_pricelist() {
    // Opens the wizard for importing Vendor Pricelists.
        this.action.doAction({
            name: "Import Vendor Pricelist",
            type: "ir.actions.act_window",
            res_model: "import.vendor.pricelist",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_pos() {
    // Opens the wizard for importing POS Orders.
        this.action.doAction({
            name: "Import POS",
            type: "ir.actions.act_window",
            res_model: "import.pos.order",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_attendance() {
    // Opens the wizard for importing Attendance records.
        this.action.doAction({
            name: "Import Attendance",
            type: "ir.actions.act_window",
            res_model: "import.attendance",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_payment() {
    // Opens the wizard for importing Payments.
        this.action.doAction({
            name: "Import Payment",
            type: "ir.actions.act_window",
            res_model: "import.payment",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_task() {
    // Opens the wizard for importing Project Tasks.
        this.action.doAction({
            name: "Import Task",
            type: "ir.actions.act_window",
            res_model: "import.task",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_sales_pricelist() {
    // Opens the wizard for importing Sales Pricelists.
        this.action.doAction({
            name: "Import Sales Pricelist",
            type: "ir.actions.act_window",
            res_model: "import.sales.pricelist",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_inventory() {
    // Opens the wizard for importing Inventory without Lot/Serial numbers.
        this.action.doAction({
            name: "Import Inventory without Lot and Serial Number",
            type: "ir.actions.act_window",
            res_model: "import.inventory",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }

    import_inventory_with_lot() {
    // Opens the wizard for importing Inventory with Lot/Serial numbers.
        this.action.doAction({
            name: "Import Inventory with Lot and Serial Number",
            type: "ir.actions.act_window",
            res_model: "import.inventory.with.lot",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }
}

// This line is CRUCIAL - registers your dashboard so Odoo can find it
actionRegistry.add("import_dashboard_tag", ImportDashBoard);