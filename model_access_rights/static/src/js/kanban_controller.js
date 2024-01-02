odoo.define('model_access_rights/static/src/js/kanban_controller.js', function (require) {
'use strict';

    var KanbanController = require('web.KanbanController');
    const { patch } = require('web.utils');
    var rpc = require('web.rpc');

    const components = {
        KanbanController: require('web.KanbanController'),
    };

    patch(components.KanbanController, 'model_access_rights/static/src/js/kanban_controller.js.KanbanController', {
    /**
    * This function will used to hide the selected options from the kanban view
    */
        async willStart() {
            var self = this;
            var user_id = self.initialState.context.uid;
            var model = self.modelName;
            await rpc.query({model: 'access.right', method: 'hide_buttons',
                args: [[user_id, model]],
            }).then(function(data) {
                if(data){
                    if(data['is_create_or_update']){
                        self.activeActions.create = false;
                        self.activeActions.edit = false;
                    }
                    if(data['is_delete']){
                        self.activeActions.delete = false;
                    }
                    if(data['is_archive']){
                        self.archiveEnabled = false;
                    }
                }
            });
        },
    });
});
