/** @odoo-module */
import {Component, useState, onMounted, useRef} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";

export class ChoosePicking extends Component {
    static components = {Dialog, Many2XAutocomplete}
    static template = "choosePicking"

    setup() {
        this.state = useState({
            picking: 0,
            pickingId: false,
            pickingName: ""

        })
        this.root = useRef("root")
        onMounted(() => {
            this.root.el.querySelector(".o-autocomplete--input")?.focus()
        })
    }
    update(value){
        this.state.pickingId = value[0]?.id;
        this.state.pickingName = value[0]?.display_name;
    }

    get pickingProps() {
        return {
            resModel: 'stock.picking',
            getDomain: () => [['id', 'in', this.props.pickingIds]],
            fieldString: "Picking",
            value: this.state.pickingName,
            update: this.update.bind(this),
            activeActions: {}
        }
    }
    async applyPicking(){
        await this.props.assignPicking(this.state.pickingId)
        this.props.close()
    }

}

