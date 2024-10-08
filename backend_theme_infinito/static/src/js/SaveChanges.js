/** @odoo-module **/
// Import necessary components and functionalities from Odoo libraries
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
const { useRef, onWillStart, xml ,onMounted} = owl;
import { useService,useBus } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";
import { browser } from "@web/core/browser/browser";
// Define the SaveChanges component
export class SaveChanges extends Component{
    setup() {
        // Initialize action service
        this.actionService = useService("action");
    }
    // Method to handle apply button click event
    async _onClickApply(){
        // Retrieve modified styles data and target class from props
        var self = this;
         var styles = this.props.tools;
         var changed_styles = [];
         for (var i = 0; i < styles.length; i++) {
             changed_styles.push(styles[i]);
         }
         var changed_style_json = {};
         for (var i in changed_styles) {
            changed_style_json[changed_styles[i]] = styles[changed_styles[i]];
         }
         // Send modified styles data to the server for saving
         await jsonrpc('/theme_studio/save_styles',{
            method:'call',
            kwargs:{
                'changed_styles': JSON.stringify(changed_style_json),
                'object_class': self.props.targetClass,
            }
         })
         // Trigger browser location change to reload assets in debug mode
         browser.location.search = "?debug=assets";
         // Close the dialog
         this.env.dialogData.close();
    }
    // Method to handle dialog close event
    handleCloseDialog() {
        // Close the dialog
        this.env.dialogData.close();
    }
}
// Define template for SaveChanges component
SaveChanges.template = "backend_theme_infinito.saveChanges";
// Define components used in SaveChanges component
SaveChanges.components = { Dialog };
// Define props for SaveChanges component
SaveChanges.props = {
    confirmLabel: { type: String, optional: true },
    confirmClass: { type: String, optional: true },
    cancelLabel:{ type: String, optional:true},
    tools: Object,
    targetClass: { type: String, optional: true },
    close: { type: Function, optional: true },
};
// Default props for SaveChanges component
SaveChanges.defaultProps = {
    confirmLabel: _t("Save"),
    confirmClass: "btn-primary",
    cancelLabel:_t("Discard")
};
