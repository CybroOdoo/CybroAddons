/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";


publicWidget.registry.websiteLimit = publicWidget.Widget.extend({
    selector: '.venue-booking-widget',
    events: {
        'click #check': '_onCheckClick',
        'click #next': '_onNextClick',
        'change #venue_type': '_onChangeVenue',
    },
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },
    _onCheckClick: function(ev) { //Click function to fetch from and to location value and calculate the distance.
        var self = this
        var location = this.el.querySelector('#location').value
        if (location != '') {
            this.el.querySelector('#loader').classList.remove("d-none");
            ajax.jsonRpc('/geo/' + location, 'call', {}).then(function(data) { // success callback
                self.el.querySelector('#loader').classList.add("d-none");
                self.el.querySelector('#details').classList.remove("d-none");
            }).catch(function(data) {
                self.el.querySelector('#loader').classList.add("d-none");
                Dialog.alert(this, "Please enter valid city");
                return false;
            });
        } else {
            Dialog.alert(this, "Add a City");
            return false;
        }
    },
    _onNextClick: function(ev) { //Function to show the customer details form view
        var self = this;
        var start_date = self.$el.find('#from_date').val();
        var end_date = self.$el.find('#to_date').val();
        var venue_type = self.$el.find('#venue_type').val();
        var domain = [
            ['start_date', '<', end_date],
            ['end_date', '>', start_date],
            ['venue_id', '=', venue_type],
        ];
        this.orm.call('venue.booking', 'search', [domain])
            .then(function(result) {
                if (result.length>0) {
                    const open_deactivate_modal = true;
                    const modalHTML = `
                            <div class="modal ${open_deactivate_modal ? 'show d-block' : ''}" id="popup_error_message" tabindex="-1" role="dialog">
                                <div class="modal-dialog" role="document">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <button type="button" class="btn-close" data-dismiss="modal"></button>
                                        </div>
                                        <form class="oe_login_form modal-body" role="form">
                                            Venue is not available for the selected time range.
                                        </form>
                                    </div>
                                </div>
                            </div>
                        `;
                    $("body").append(modalHTML);
                    $("body").find("#popup_error_message").find(".btn-close").on("click", function() {
                        $("body").find("#popup_error_message").remove();
                    });
                } else {
                    self.el.querySelector('#customer').classList.remove("d-none");
                }
            });
    },
    _onChangeVenue: function(event) { //Function for getting popup message for date
        var self = this;
        var start_date = self.$el.find('#from_date').val();
        var end_date = self.$el.find('#to_date').val();
        if (start_date > end_date) {
            event.preventDefault();
            const open_deactivate_modal = true;
            const modalHTML = `
                            <div class="modal ${open_deactivate_modal ? 'show d-block' : ''}" id="popup_error_message" tabindex="-1" role="dialog">
                                <div class="modal-dialog" role="document">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <button type="button" class="btn-close" data-dismiss="modal"></button>
                                        </div>
                                        <form class="oe_login_form modal-body" role="form">
                                            Start date must be less than End date.
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
    },
})
