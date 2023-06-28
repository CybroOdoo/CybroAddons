odoo.define('delivery_date_scheduler_odoo.portal_content', function(require) {
    "use strict";
    var rpc = require('web.rpc');
    var PublicWidget = require('web.public.widget');
    var Dialog = require('web.Dialog');
    var Template = PublicWidget.Widget.extend({
        selector: '.delivery_schedule_portal_content',
        events: {
            'change #delivery_note': '_onChangeDeliveryNote',
            'change #delivery_date': '_onChangeDeliveryDate',
            'click #confirm': '_onClickConfirm',
        },
        /**
         * getting input data from delivery_note
         */
        _onChangeDeliveryNote: function(ev) {
            this.input_comment = ev.currentTarget.value
        },
        /**
         * getting input data from delivery_date and transfer to checking
         */
        _onChangeDeliveryDate: function(ev) {
            this.input_date = ev.currentTarget.value
            var self = this;
            this.el.querySelector("#error_for_date").innerHTML = "";
            rpc.query({
                model: 'res.config.settings',
                method: 'delivery_date_schedule',
                args: [, this.input_date],
            }).then(function(data) {
                self.error_value = data.error_value
                self.min_date = data.min_date
                self.max_date = data.max_date
                if (self.error_value == 2) {
                    self.el.querySelector("#error_for_date").innerHTML = "* the delivery date must between " + self.min_date + " and " + self.max_date
                }
            });
        },
        /**
         * confirming the quotation and updating the value
         */
        _onClickConfirm: function(ev) {
            var self = this;
            if (!this.error_value) {
                Dialog.alert(self, "please provide the delivery date");
                return false;
            } else if (this.error_value == 2) {
                Dialog.alert(self,  "please provide the delivery date between " + self.min_date + " and " + self.max_date);
                return false;
            } else {
                rpc.query({
                    model: 'sale.order',
                    method: 'confirm_delivery_date_schedule',
                    args: [, {
                        'id': ev.currentTarget.getAttribute("value"),
                        'date': self.input_date,
                        'description': self.input_comment
                    }],
                })
                window.location = "/my/home"
            }
        }
    })
    PublicWidget.registry.delivery_schedule_portal_content = Template;
    return Template;
})