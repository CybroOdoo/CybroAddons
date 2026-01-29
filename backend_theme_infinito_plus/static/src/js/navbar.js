/** @odoo-module **/
import ControlPanel from "web.ControlPanel";
import { patch } from 'web.utils';
var session = require('web.session');
//Patching the ControlPanel for adding new clicks
patch(ControlPanel.prototype, 'backend_theme_infinito_plus/static/src/js/navbar.js', {
    //Function to refresh the model data.
    onRefreshClick(){
       this.model.dispatch()
    },
    //Function for enable and disable the refresh button in  navbar.
    RefreshOn(){
        return session.infinitoRefresh;
    }
})