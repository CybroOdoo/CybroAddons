/** @odoo-module **/
import { FloatField } from '@web/views/fields/float/float_field';
import { registry } from "@web/core/registry";
const { onRendered, useRef, onMounted } = owl;
import { useService } from "@web/core/utils/hooks";
import { _lt } from "@web/core/l10n/translation";
import { xml, Component, useState } from "@odoo/owl";
import AbstractField from 'web.AbstractField';
import fieldRegistry from 'web.field_registry';
/** Extends FloatField to create ProgressBarWidget to create a widget for float fields **/
export class ProgressBarWidget extends FloatField {
    setup() {
        super.setup();
        this.state = useState({
                range: this.props.value || '',
        });
	    this.orm = useService("orm");
        const Pro_Ref = useRef("Progress-Ref");
        onMounted(() => {
            this.ref = Pro_Ref.el
            this.UpdateBar()
        });
    }
    /** Updates the percentage based on value in bar **/
    UpdateBar() {
        var value = this.state.range;
        var max_value = 100;
        value = value || 0;
        var widthComplete;
        if (value <= max_value) {
            widthComplete = parseInt(value/max_value * 100);
        }else{
            widthComplete = 100;
        }
        $(this.ref.querySelector('.progress_number')).text(widthComplete.toString() + '%');
    }
    /** Change function of progress **/
    async _onChangeRange(value){
        var field = this.props.name
        console.log("this.props.name", this.props.name)
        this.props.value = value
        this.state.range = value
        this.UpdateBar()
        await this.orm.write(this.env.model.root.resModel, [this.env.model.root.data.id], {
            [field]: this.state.range,
        })
    }
}
ProgressBarWidget.supportedTypes = ["float"];
ProgressBarWidget.template = xml
` <div t-ref="Progress-Ref">
     <div class="progress_bar d-flex">
        <div>
            <input type="range" class="pro-bar" id="customRange1" min="0" max="100"
            t-on-change="(ev)=>this._onChangeRange(ev.target.value)" t-att-value="this.props.value"/>
        </div>
        <div>
            <span class="progress_number"><t t-esc="this.props.value"/></span>
        </div>
     </div>
  </div>`
registry.category("fields").add("progress_bar_widget", ProgressBarWidget);
