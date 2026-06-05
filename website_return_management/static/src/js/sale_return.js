/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
/**
 * Widget for managing return order actions on the website quote page.
 * Handles the display of the return modal and validates product selection.
 */
publicWidget.registry.return_order = publicWidget.Widget.extend({
    selector: '#quote_content',
    events: {
        'click #hidden_box_btn': '_onHiddenBoxBtnClick',
        'change #product': '_onProductChange',
    },
    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
    },
    /**
     * Handles the click event for showing the hidden box modal.
     * @private
     * @param {Event} ev
     */
    _onHiddenBoxBtnClick: function (ev) {
        ev.preventDefault();
        this.$('#hidden_box').modal('show');
    },
    /**
     * Handles the change event for the product selection.
     * Toggles the 'submit' button visibility based on whether a product is selected.
     * @private
     * @param {Event} ev
     */
    _onProductChange: function (ev) {
        var $product = $(ev.currentTarget);
        this.$('#submit').toggleClass('d-none', $product.val() === 'none');
    },
});