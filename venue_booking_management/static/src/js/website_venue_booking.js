/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.websiteLimit = publicWidget.Widget.extend({
    selector: '.venue-booking-widget',
    events: {
        'click #next': '_onNextClick',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },

    _onNextClick: function (ev) {
        var self = this;

        var start_date = self.$el.find('#from_date').val();
        var end_date = self.$el.find('#to_date').val();
        var venue_type = self.$el.find('#venue_type').val();

        // ✅ Let browser handle empty validation using "required"
        if (!start_date || !end_date || !venue_type) {
            return; // browser will show "Please fill out this field"
        }

        // ✅ Proper date comparison
        if (new Date(start_date) >= new Date(end_date)) {
            alert("End Date must be after Start Date");
            return;
        }

        // ✅ Only availability check (NO big popup)
        var domain = [
            ['start_date', '<', end_date],
            ['end_date', '>', start_date],
            ['venue_id', '=', parseInt(venue_type)],
            ['state', 'not in', ['cancel', 'close']]
        ];

        this.orm.call('venue.booking', 'search', [domain]).then(function (result) {
            if (result.length > 0) {
                alert("Venue is not available for the selected time range.");
            } else {
                self.el.querySelector('#customer').classList.remove("d-none");
            }
        });
    },
});
