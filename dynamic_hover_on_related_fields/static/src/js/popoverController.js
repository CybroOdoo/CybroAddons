/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { onWillStart, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Tooltip } from "@web/core/tooltip/tooltip";

patch(Tooltip.prototype, {
    setup(){
        if (super.setup) {
            super.setup();
        }
        this.orm = useService("orm");
        this.hoverState = proxy({ requiredData: null });
        onWillStart(async () => await this.getDataFromBackend());
    },
    async getDataFromBackend() {
        if (!this.props.info?.field?.relation) return;
        if (this.props.info?.related_record_id){
            this.hoverState.requiredData = await this.orm.call(
            "hover.related.fields",
            "finding_the_data_to_show_tooltip_many2many",
            [this.props.info]);
        }else if(this.props.info?.resId){
            this.hoverState.requiredData = await this.orm.call(
            "hover.related.fields",
            "finding_the_data_to_show_tooltip",
            [this.props.info]);
        }
    }
});
