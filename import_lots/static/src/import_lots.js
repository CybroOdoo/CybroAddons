/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { Component, xml, useProps } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

/**
 *  Extended and added new widget to the registry
 */
class ImportLots extends Component {
    static template = xml`<button class="btn btn-secondary w-100" t-if="this.isVisible" t-on-click="this.openDialog">Import Lots from Sheet</button>`;
    props = useProps(standardWidgetProps);

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
    }

    get isVisible() {
        return this.props.record?.data?.state !== "done";
    }

    openDialog(ev) {
        const record = this.props.record;
        const recordData = record.data;
        const productId = recordData.product_id?.id || (Array.isArray(recordData.product_id) ? recordData.product_id[0] : recordData.product_id);
        const pickingId = recordData.picking_id?.id || (Array.isArray(recordData.picking_id) ? recordData.picking_id[0] : recordData.picking_id) || record.context?.default_picking_id;
        const moveId = record.resId || recordData.id || record.context?.default_move_id;

        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Import Lots",
            res_model: "lot.attachment",
            view_mode: "form",
            views: [
                [false, "form"]
            ],
            target: "new",
            context: {
                default_product_id: productId,
                default_demanded_quantity: recordData.product_uom_qty,
                default_picking_id: pickingId,
                default_move_id: moveId,
            },
        });
    }
}

registry.category("view_widgets").add("import_lot", { component: ImportLots });