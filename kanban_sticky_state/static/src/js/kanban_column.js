odoo.define('kanban_sticky_state.kanban_column', function (require) {
"use strict";

    var KanbanColumn = require('web.KanbanColumn');
    var session = require('web.session');
    /**
    Include KanbanColumn to add class for sticky state of kanban
    **/
    KanbanColumn.include({
        /** To start the KanbanColumn for kanban sticky state **/
        start: function () {
        this._super.apply(this, arguments)
             if (session.is_kanban_sticky_state) {
                this.$header[0].classList.add("is_kanban_sticky_state");
            } else {
                this.$header[0].classList.remove("is_kanban_sticky_state");
            }
        }
    });
    return KanbanColumn;
});
