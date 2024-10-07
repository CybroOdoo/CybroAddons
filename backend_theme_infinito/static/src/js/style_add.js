/** @odoo-module **/
// Importing necessary modules and components
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
const { useRef, onWillStart, xml ,onMounted} = owl;
import { useService, useBus } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { NewTools } from "./change"
// Dictionary to store design styles
const DesignDictionary = {}
// Component definition for InfinitoDialog
export class InfinitoDialog extends Component{
    // Setup method to initialize component state and services
    setup() {
        this.actionService = useService("action");
        this.state = useState({
            searchValue: '',
            style:DesignDictionary,
        });
        this.current_tools = [];
    }
    /**
     * Method to handle change event on search input
     * @param {Event} ev - The event object
     */
    _onChange (ev){
        this.state.searchValue = ev.target.value;
    }
     /**
     * Method to add selected tool to design dictionary
     */
    add (){
        var val = document.querySelector('select').value;
        for (var i = 0; i < NewTools.property.length; i++) {
            for (var key in NewTools.property[i]) {
               if (val.includes(NewTools.property[i][key]) && key === 'name' && NewTools.property[i][key] === val) {
                    DesignDictionary[val] = NewTools.property[i];
                    break;
                }
            }
        }
        // Triggering render event with updated style configuration
        this.env.bus.trigger('renderEvent', { "config": this.state.style })
        this.current_tools.push(val);
        // Closing the dialog
       this.env.dialogData.close();
    }
}
// Template definition for InfinitoDialog
InfinitoDialog.template = "backend_theme_infinito.StyleAdd";
// Registering Dialog component as a child component
InfinitoDialog.components = { Dialog };
// Prop definitions for InfinitoDialog
InfinitoDialog.props = {
    confirmLabel: { type: String, optional: true },
    confirmClass: { type: String, optional: true },
    tools: Object,
    close: { type: Function, optional: true },
    };
// Default props for InfinitoDialog
InfinitoDialog.defaultProps = {
    confirmLabel: _t("ADD"),
    confirmClass: "btn-primary",
};
