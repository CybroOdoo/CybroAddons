/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
var ajax = require('web.ajax');
var core = require('web.core');
var qweb = core.qweb;

var GetUser = Widget.extend({
    /**
    function run before loading the page to call methode "get_idle_time"
    */
    willStart: function() {
        var self = this;
        return this._super().then(function() {
            self.get_user();
        });
    },
    /**
    Getting minutes through python for the corresponding user in the backend
    */
    get_user: function() {
        var self = this
        var now = new Date().getTime();
        ajax.rpc('/get_ip').then(function(data) {
           console.log(data)
           if (data == false){
              location.replace("/web/session/logout")
           }
        })
    },
});
SystrayMenu.Items.push(GetUser);
export default GetUser;