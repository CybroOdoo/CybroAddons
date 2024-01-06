odoo.define('bill_digitization.tree_button', function (require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');
    const session = require('web.session');
    var TreeButton = ListController.extend({
    /* Assigning a default value to the button_state */
        state: {
            button_state : false
        },
        /* Retrieves the current value of the button state from the session. */
        get_button_value: function(){
            return session.button_state
        },
       buttons_template: 'bill_digitization.buttons',
       /* Click event to pop up a wizard */
       events: _.extend({}, ListController.prototype.events, {
           'click .open_wizard_action': '_OpenWizard',
       }),
       /* Function that calling upon clicking the button */
       _OpenWizard: function () {
            var self = this;
            self.do_action({
               type: 'ir.actions.act_window',
               res_model: 'digitize.bill',
               name :'Upload Bill',
               view_mode: 'form',
               view_type: 'form',
               views: [[false, 'form']],
               target: 'new',
               res_id: false,
           });
       },
    });
    /* Adding the button into specific view */
    var AccountMoveListView = ListView.extend({
       config: _.extend({}, ListView.prototype.config, {
           Controller: TreeButton,
       }),
    });
    viewRegistry.add('button_in_tree', AccountMoveListView);
    });
