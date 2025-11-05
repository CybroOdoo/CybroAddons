odoo.define('game_sudoku.models_entertainment_game', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;


var MyGame = Widget.extend({
    events: {
        "click .o_entertainment_games_log_in_icon": function() {
            this.$('.o_entertainment_games_log_in_icon').attr("disabled", "disabled");
            this.$('.o_entertainment_games_req_footer').css('display', 'block');
            this.game_request();
        },
    },

    start: function () {
        var self = this;

        var def = this._rpc({
                model: 'hr.employee',
                method: 'search_read',
                args: [[['user_id', '=', this.getSession().uid]], ['attendance_state', 'name']],
            })
            .then(function (res) {
                if (_.isEmpty(res) ) {
                    self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                    return;
                }
                self.employee = res[0];
                self.$el.html(QWeb.render("EntertainmentGamesMainMenu", {widget: self}));
            });

        return $.when(def, this._super.apply(this, arguments));
    },

    game_request: function () {
        var self = this;
        this._rpc({
                model: 'employee.game.approve',
                method: 'create_employee_game_approve',
                args: [1, this.employee.id, this.getSession().uid],
            })
    },
});

core.action_registry.add('entertainment_games_my_game', MyGame);

return MyGame;

});