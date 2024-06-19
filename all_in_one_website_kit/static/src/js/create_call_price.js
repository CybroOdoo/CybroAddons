odoo.define('all_in_one_website_kit.create', function(require) {
    "use strict";
    var rpc = require('web.rpc');
    var PublicWidget = require('web.public.widget');
    var Dialog = require('web.Dialog');
    /** Extends the public widget class to add the events
    */
    var Template = PublicWidget.Widget.extend({
        selector: '#call_for_price',
        events: {
            'click #send_btn': '_onClickActionSend'
        },
        /**
        while clicking the send button creating the record in the backend
        */
        _onClickActionSend: function() {
            var first = this.$el.find('#first_name').val();
            var last = this.$el.find('#last_name').val();
            var product_id = this.$el.find('#product_id').val();
            var phone = this.$el.find('#phone').val();
            var email = this.$el.find('#email').val();
            var message = this.$el.find('#message').val();
            var qty = this.$el.find('#quantity').val();
            if(first && last && product_id && phone && email && message && qty) {
                this.el.style.display = 'none';
                var self = this;
                rpc.query({
                    model: "call.price",
                    method: "create_form",
                    args: [first, last, product_id, phone, email, message, qty]
                }).then(function(result) {
                    document.getElementById('alert_message').style.display = "block"
                });
            }else{
                Dialog.alert(self, "please fill the required fields");
            }
        }
    });
    PublicWidget.registry.call_for_price = Template;
    return Template;
})