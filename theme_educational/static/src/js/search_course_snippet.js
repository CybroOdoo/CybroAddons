import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SearchCourseSnippet = publicWidget.Widget.extend({
    selector: '.o_search_course_snippet',

    events: {
        'click .o_search_course_btn': '_onSearchClick',
        'keypress .o_search_course_input': '_onKeyPress',
    },

    /**
     * Redirect to shop page with search query
     */
    _redirectToShop() {
        const searchValue = this.$('.o_search_course_input').val().trim();

        window.location.href = '/shop?search=' + encodeURIComponent(searchValue);
    },

    /**
     * Handle search button click
     */
    _onSearchClick(ev) {
        ev.preventDefault();
        this._redirectToShop();
    },

    /**
     * Handle enter key press
     */
    _onKeyPress(ev) {
        if (ev.which === 13) {
            ev.preventDefault();
            this._redirectToShop();
        }
    },
});
