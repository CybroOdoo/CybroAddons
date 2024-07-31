/** @odoo-module **/
import LegacyControlPanel from "web.ControlPanel";
import {patch} from "web.utils";
import session from 'web.session';
const { onMounted } = owl.hooks;
patch(
    LegacyControlPanel.prototype,
    "hide_filters_groupby.LegacyControlPanel",
    {
        components: {
            ...LegacyControlPanel.components,
        },
        setup() {
            this._super();
            if (session.is_hide_filters_groupby_enabled == 'True'){
                if (session.hide_filters_groupby == 'global'){
                    onMounted(this.hide_globally)
                } else if (session.hide_filters_groupby == 'custom'){
                    onMounted(this.hide_on_custom)
                }
            }
        },
        /**
     * Customized method to hide filter and groupby options globally.
     * This method is called when the 'session.hide_filters_groupby_is_enabled' is 'True' and
     * 'session.hide_filters_groupby' is set to 'global'.
     */
        //hides filter and groupby options globally
    hide_globally(){
        this.vnode.elm.querySelector('.o_search_options').style.display = 'none';
    },
        //hides filter and groupby options on custom choice
        /**
     * Customized method to hide filter and groupby options  based on custom settings.
     * This method is called when the 'session.hide_filters_groupby_is_enabled' is 'True' and
     * 'session.hide_filters_groupby' is set to 'custom'.
     */
    hide_on_custom(){
        if (this.parent.props.searchModel) {
            this.parent.props.searchModel.env.services.rpc({
                model: 'ir.model',
                method: 'search_read',
                args: [[["model", "=", this.parent.props.action.res_model]]],
            }).then((value) => {
                if (eval(session.ir_model_ids).includes(value[0].id)) {
                    if (this.vnode.elm) {
                        this.vnode.elm.querySelector('.o_search_options').style.display = 'none';
                    }
                }
            });
        }
    }
});