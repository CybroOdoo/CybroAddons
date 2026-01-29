/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import ajax from 'web.ajax';
import core from 'web.core';
var qweb = core.qweb;

var GetUser = Widget.extend({
    /**
    function run before loading the page to call method "get_user"
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
        var self = this;
        ajax.rpc('/get_ip').then(function(data) {
           if (data == false){
              location.replace("/web/session/logout")
           }
        });
    },
    /**
    Binding mouseup event
    */
    start: function() {
        var self = this;
        this._super.apply(this, arguments).then(function() {
            $(document).on('mouseup', self.onMouseUp.bind(self));
        });
    },
    /**
    Function to be called on mouseup event
    */
    onMouseUp: function(event) {
        this.get_user();
    },
});

// Ensure the widget is added to the Systray menu
SystrayMenu.Items.push(GetUser);
export default GetUser;
