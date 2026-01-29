odoo.define('import_images_from_zip_file.FileImport', function (require) {
"use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');
    var _t = core._t;
    /**
    * ListController used to bind button with list view
    */

    ListController.include({
        renderButtons: function($node) {
           this._super.apply(this, arguments);
               if (this.$buttons) {
                 this.$buttons.find('.new').click(this.proxy('view_wizard')) ;
               }
        },
        view_wizard: function () {
            this.do_action({
                _name : _t('View Wizard'),
                type: 'ir.actions.act_window',
                res_model: 'import.image',
                views: [[false, 'form']],
                view_mode: 'form',
                context: {
                default_model_template:this.modelName,
                },
                target: 'new',
            });
        }
    })
});