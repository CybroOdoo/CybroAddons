import { t, useProps } from "@odoo/owl";
import { Component, proxy, usePlugin } from "@odoo/owl";
/** @odoo-module **/

import {Dialog} from "@web/core/dialog/dialog";
import {_t} from "@web/core/l10n/translation";
import {NewTools} from "./change"


const DesignDictionary = {}

export class InfinitoDialog extends Component {
    props = useProps({
        confirmLabel: t.string().optional(_t("ADD")),
        confirmClass: t.string().optional("btn-primary"),
        tools: t.any(),
        targetClass: t.string().optional(),
        close: t.function().optional(),
    });
    setup() {
        this.state = proxy({
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
        this.props.close();
    }
}

InfinitoDialog.template = "backend_theme_infinito.StyleAdd";
InfinitoDialog.components = {Dialog};

