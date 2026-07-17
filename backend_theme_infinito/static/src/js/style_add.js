/** @odoo-module **/
import {Component, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";
import {NewTools} from "./change"

const DesignDictionary = {}

export class InfinitoDialog extends Component {
    setup() {
        this.actionService = useService("action");
        this.state = useState({
            searchValue: '',
            style: DesignDictionary,
        });
        this.current_tools = [];
    }

    /**
     * Method to handle change event on search input
     * @param {Event} ev - The event object
     */
    _onChange(ev) {
        this.state.searchValue = ev.target.value;
    }

    /**
     * Method to add selected tool to design dictionary
     */
    add() {
        var val = document.querySelector('select').value;
        for (var i = 0; i < NewTools.property.length; i++) {
            for (var key in NewTools.property[i]) {
                if (val.includes(NewTools.property[i][key]) && key === 'name' && NewTools.property[i][key] === val) {
                    DesignDictionary[val] = NewTools.property[i];
                    break;
                }
            }
        }
        this.env.bus.trigger('renderEvent', {"config": this.state.style})
        this.current_tools.push(val);
        // Closing the dialog
        this.env.dialogData.close();
    }
}

InfinitoDialog.template = "backend_theme_infinito.StyleAdd";
InfinitoDialog.components = {Dialog};
InfinitoDialog.props = {
    confirmLabel: {type: String, optional: true},
    confirmClass: {type: String, optional: true},
    tools: Object,
    close: {type: Function, optional: true},
};
InfinitoDialog.defaultProps = {
    confirmLabel: _t("ADD"),
    confirmClass: "btn-primary",
};
