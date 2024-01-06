/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.websiteLimit = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click a[name="website_sale_main_button"]': '_onCheckoutButtonClick',
    },
    /**
     * When the total amount is less than the limit applied in the configuration settings, an error popup window appears.
     *
     * @override
     */
    init() {
        this._super(...arguments);
    },
//    Method to check the purchase minimum limit
    _onCheckoutButtonClick(event) {
        if (this.$el.find("#website_purchase_limit_value").length) {
            event.preventDefault();
            const limit = parseFloat(this.$el.find("#website_purchase_limit_value").attr("limit"));
            const open_deactivate_modal = true;
            // HTML modal structure
            const modalHTML = `
            <div class="modal ${open_deactivate_modal ? 'show d-block' : ''}" id="popup_error_message" tabindex="-1" role="dialog">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5>The purchase amount did not meet the limit!</h3>
                            <button type="button" class="btn-close" data-dismiss="modal"></button>
                        </div>
                        <form class="modal-body" role="form">
                            The purchase amount must be greater than the limit
                            <b>
                                <span>${limit}</span>
                            </b>
                        </form>
                    </div>
                </div>
            </div>
            `;
            $("body").append(modalHTML);
            $("body").find("#popup_error_message").find(".btn-close").on("click", function() {
                $("body").find("#popup_error_message").remove();
            });
        }
    }
})
