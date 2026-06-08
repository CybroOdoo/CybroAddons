/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";


const SaleReturn = publicWidget.Widget.extend({
    selector: '.sale_return_template',
    events: {
        'click #hidden_box_btn': '_onClickShowModal',
        'change #product': '_onChangeProduct',
    },
    /**
    for showing the modal
    */
    _onClickShowModal: function () {
        this.$('#hidden_box').modal('show');
    },
    /**
    while changing the product editing the style
    */
    _onChangeProduct: function () {
        var button_submit = this.$('#submit');
        button_submit.addClass('d-none');
        if (this.$("#product").val() == 'none') {
            if (!button_submit.hasClass('d-none')) {
                button_submit.addClass('d-none');
            }
        } else {
            if (button_submit.hasClass('d-none')) {
                button_submit.removeClass('d-none');
            }
        }
    }
});

publicWidget.registry.sale_return_template = SaleReturn;
export default SaleReturn;