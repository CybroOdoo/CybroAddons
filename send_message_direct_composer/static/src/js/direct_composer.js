odoo.define('mail.send_message_direct_composer', function (require) {
"use strict";
    var chat_manager = require('mail.chat_manager');
    var chatter = require('mail.Chatter');
    chatter.include({
        on_open_composer_new_message: function () {
            var self = this;
            this.on_open_composer();
            },
        on_open_composer: function() {
            var self = this;
            var context = {};

            if (self.context.default_model && self.context.default_res_id) {
                context.default_model = self.context.default_model;
                context.default_res_id = self.context.default_res_id;
            }

            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'mail.compose.message',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: context,
            }, {
                on_close: function() {
                    self.trigger('need_refresh');
                    var parent = self.getParent();
                    chat_manager.get_messages({model: parent.model, res_id: parent.res_id});
                },
            }).then(self.trigger.bind(self, 'close_composer'));

        }

    });
});