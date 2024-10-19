/** @odoo-module **/
import { Dialog } from '@web/core/dialog/dialog';
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { Component, xml } from "@odoo/owl";

/**
 *  Extended and added new widget to the registry
 */
class ImportLots extends Component {
        static template = xml`<button class="btn btn-link"  t-if="this.isVisible" t-on-click="openDialog">Import Lots from Sheet</button>`;
    setup(){
        this.action = useService("action");
        this.orm = useService("orm");
    }
    get isVisible() {
        return this.props.record.data.state !== 'done';
    }
    openDialog(ev){
        this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: 'Import Lots',
                    res_model: 'lot.attachment',
                    view_mode: 'form',
                    views: [
                        [false, 'form']
                    ],
                    target: 'new',
                    context:{
                    default_product_id: this.props.record.data.product_id[0],
                    default_demanded_quantity: this.props.record.data.product_uom_qty,
                    default_picking_id: this.props.record.data.picking_id[0],
                    default_move_id: this.props.record.data.move_line_ids._config.context.default_move_id
                    }
                })
    }
}
registry.category("view_widgets").add("import_lot", {component: ImportLots});
