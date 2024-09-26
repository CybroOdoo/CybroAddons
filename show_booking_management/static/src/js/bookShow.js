/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.bookShow = publicWidget.Widget.extend({
    /* Extending widget and creating book show */
    selector: '.book_show',
    events: {
        'change #choose_date' : 'CheckShows',
    },
    CheckShows: function (ev) {
        /* Function for validating date. */
        const selectedDate = new Date(ev.currentTarget.value);
        const currentDate = new Date();
        selectedDate.setHours(0, 0, 0, 0);
        currentDate.setHours(0, 0, 0, 0);
        const movieId = this.$el.find('form')[0].dataset.movieId
        this.$el.find('form')[0][4].value = ''
        if (selectedDate < currentDate){
            ev.currentTarget.value = ''
            this.$el.find('#error_box').text('Please select a date in the future!')
            this.$el.find('#error_box').show()
        }
        else{
            this.$el.find('#error_box').hide()
            this.checkShowsOnDate(ev, selectedDate, movieId);
        }
    },

    checkShowsOnDate: function (ev, date, movieId) {
        /* Function for checking shows on the selected date. */
        const formattedDate = new Date(date.getTime() - (date.getTimezoneOffset() * 60000))
                          .toISOString().split('T')[0];
        return jsonrpc("/web/dataset/call_kw", {
            model: 'movie.movie',
            method: 'check_shows_on_date',
            args: [formattedDate,movieId],
            kwargs: {}
        }).then((result) => {
            if (!result){
                ev.currentTarget.value = ''
                this.$el.find('#error_box').text('There is no shows on the selected date!!')
                this.$el.find('#error_box').show()
                this.$el.find('.tickets_section').hide()
            }
            else{
                this.$el.find('.tickets_section').show()
            }
        })
    },
});
