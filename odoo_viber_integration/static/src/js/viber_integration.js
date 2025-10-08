/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
var rpc = require('web.rpc');
var ViberSystray = Widget.extend({
        /**
         *  Get users name in selection.
         */
    template: 'ViberSystray',
    events: {
       "click #toggle_icon": "_onClick",
       "click #close_viber": "_onClose",
       "change #user_select": "_changeUser"
        },
   // Call rpc query to the function and return datas to frontend
    start: function(){
            var self = this;
            this.$el.find("#viber_msg_form").hide();
               rpc.query({
               model: 'res.users',
               method: 'get_users',
               args: [0],
           })
               .then(function result(e){
                var select = self.$('#user_select');
                var option = $('<option>').attr('selected','selected').text("Choose user to contact..");
                     select.append(option);
                for (var i = 0; i < e.users.length; i++) {
                     var option = $('<option>').val(e.users[i].phone);
                     option.text(e.users[i].name);
                     select.append(option);
                }
            })
            },
    // When click on systray icon displays a form for choosing user
    _onClick: function () {
            this.$("#viber_msg_form").show();
        },
    // When change a user opens viber chatter
    _changeUser: function(){
        if (this.$el.find("#user_select").val() != "Choose user to contact.."){
            var phone = this.$el.find("#user_select").val()
            var user_number = phone.replace('-', '').replace('(', "").replace(')', '').replace(' ', '')
            window.location.assign("viber://chat?number=" + user_number)
            }
    },
    // When click on close button closes the user selection form
    _onClose: function(){
        this.$("#viber_msg_form").hide();
    },
});
SystrayMenu.Items.push(ViberSystray);
export default ViberSystray;
