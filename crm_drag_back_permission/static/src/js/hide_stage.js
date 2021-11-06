odoo.define('crm_drag_back_permission',function(require) {

var kanbanview = require('web_kanban.KanbanView');
var Model = require('web.Model');
kanbanview.include({
render: function () {
         this._super(this);

        for (var key in this.widgets) {

            if (this.widgets[key]['title'] == 'Waiting for approval'){
            var test = this.widgets[key].$el
            test.css("display", "None");
            }

            }
    },
});
});