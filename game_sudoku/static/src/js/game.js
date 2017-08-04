odoo.define('game_sudoku.models_entertainment_game', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
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
    game_request: function(){
        new Model("employee.game.approve")
                        .call("create_employee_game_approve", [1, this.employee.id, this.user])
    },

    start: function () {
        var self = this;

        var hr_employee = new Model('hr.employee');
        hr_employee.query(['attendance_state', 'name'])
            .filter([['user_id', '=', self.session.uid]])
            .all()
            .then(function (res) {
                if (_.isEmpty(res) ) {
                    self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                    return;
                }
                self.employee = res[0];
                self.user = self.session.uid
                self.$el.html(QWeb.render("EntertainmentGamesMainMenu", {widget: self}));
            });

        return this._super.apply(this, arguments);
    },
});

core.action_registry.add('entertainment_games_my_game', MyGame);

return MyGame;

});