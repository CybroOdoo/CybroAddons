/** @odoo-module **/

    import { jsonrpc } from "@web/core/network/rpc_service";
    import publicWidget from "@web/legacy/js/public/public_widget";
    import Dialog from "@web/legacy/js/core/dialog";
    publicWidget.registry.Delivery_date = publicWidget.Widget.extend({

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
           jsonrpc('/delivery_date_schedule', {'date': this.input_date}).then(function(data) {
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
                jsonrpc('/confirm_delivery_date_schedule', {'id': ev.currentTarget.getAttribute("value"),
                        'date': self.input_date,
                        'description': self.input_comment}).then(() => window.location = "/my/home");

            }
        }
    })
