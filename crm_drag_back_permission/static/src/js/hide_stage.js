openerp.crm_drag_back_permission = function (instance) {
    var kanbanview = instance.web_kanban;
    kanbanview.KanbanView.include({
        do_process_groups: function (groups) {
            var x = [] ;
            for (var i in groups) {
                if (groups[i]['attributes']['value'][1] != 'Waiting for approval') {
                    x[i] = groups[i];
                }

            }
            this._super(x);

        },
        });
}