/** @odoo-module **/

import { patch } from "@web/core/utils/patch"
import { PopoverController } from "@web/core/popover/popover_controller";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(PopoverController.prototype, {
    setup(){
        this.orm = useService("orm");
        onWillStart(async () => await this.getDataFromBackend());
        super.setup();
    },
    /**
     * Fetches data from the backend to display in tooltips.
     * Determines whether to call the method for many2many relationships or regular fields.
     * Updates the required data in the component props.
     */
    async getDataFromBackend() {
        if (!this.props.componentProps?.info?.relation) return
        if (this.props.componentProps?.info?.related_record_id){
            const requiredData = await this.orm.searchRead(
            this.props.componentProps?.info?.relation,
            [['id',"=",this.props.componentProps?.info?.related_record_id]], []
            );
            const required111 = await this.orm.search(
            this.props.componentProps?.info?.relation,
            [['id',"=",this.props.componentProps?.info?.related_record_id]], []
            );
            this.props.componentProps.info.requiredData = requiredData[0];
        }
    }
})
