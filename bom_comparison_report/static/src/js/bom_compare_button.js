odoo.define('button_near_create.tree_button', function (require) {
    "use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var TreeButton = ListController.extend({
       buttons_template: 'bom_comparison_report.buttons',
       events: _.extend({}, ListController.prototype.events, {
           'click .open_wizard_action': '_OpenWizard',
       }),
        _OpenWizard: function () {
           var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'bom.comparison',
                name:'Open Wizard',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
            });
        }
    });
    var BOMListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: TreeButton,
        }),
    });
    viewRegistry.add('compare_button_tree', BOMListView);
});
