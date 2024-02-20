/** @odoo-module **/

import { session } from "@web/session";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
//This patch is used to hide filter and groupby option on the basis of globally or custom
patch(ControlPanel.prototype,{
    setup() {
        super.setup();
        if (session.is_hide_filters_groupby_enabled == 'True'){
            if (session.hide_filters_groupby == 'global') onMounted(async () => await this.hideGlobally());
            else if(session.hide_filters_groupby == 'custom') onMounted(async () => await this.hideOnCustom());
        }
    },
    //hides filter and groupby options globally
    hideGlobally(){
        const toggler = this.root.el.querySelector('.o_searchview_dropdown_toggler');
        const searchView = this.root.el.querySelector('.o_searchview.form-control')
        if (toggler) toggler.style.display = 'none';
        if (searchView) searchView.style.borderRadius= '5px';
    },

    //hides filter and groupby options on custom choice
    async hideOnCustom(){
        if (this.env.searchModel){
            const model_id = await this.env.services.orm.search("ir.model", [["model", "=", this.env.searchModel.resModel]], { limit: 1 });
            if (eval(session.ir_model_ids).includes(model_id[0])) await this.hideGlobally();
        }
    }
});
