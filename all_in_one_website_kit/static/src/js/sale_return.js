odoo.define('all_in_one_website_kit.return', function(require) {
    "use strict";
    var PublicWidget = require('web.public.widget');
      /** Extends the public widget class to add the events
    */
    var Template = PublicWidget.Widget.extend({
        selector: '.sale_return_template',
        events: {
            'click #hidden_box_btn': '_onClickShowModal',
            'change #product': '_onChangeProduct',
        },
        /**
        for showing the modal
        */
        _onClickShowModal: function() {
            this.$('#hidden_box').modal('show');
        },
        /**
        while changing the product editing the style
        */
        _onChangeProduct: function() {
            var button_submit = this.$('#submit');
            button_submit.addClass('d-none');
            if ($("#product").val() == 'none') {
                if (!button_submit.hasClass('d-none')) {
                    button_submit.addClass('d-none');
                }
            } else {
                if (button_submit.hasClass('d-none')) {
                    button_submit.removeClass('d-none');
                }
            }
        }
    })
    PublicWidget.registry.sale_return_template = Template;
    return Template;
});