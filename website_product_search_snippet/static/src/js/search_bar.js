/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";


publicWidget.registry.portalDetails = publicWidget.Widget.extend({
    /**
     * This widget handles search functionality within a product table on the website.
     * It listens for keyup events on the search input field and filters table rows
     * based on the user's input.
     */
    selector: '.product_search_bar',
    events: {
        'keyup .search_product_bar': '_onKeyUp',
    },
    /**
     * Initializes the widget and starts the functionality.
     *
     * @returns {Promise} - Resolves when the widget has fully started.
     */
    start: function () {
        this._super.apply(this, arguments);
    },
    /**
     * Handles the keyup event to filter table data.
     *
     * This function retrieves the value from the search input field, converts it to
     * uppercase, and then compares it with the text content of each table cell.
     * Rows that contain a match are displayed, while others are hidden.
     *
     * @private
     */
    _onKeyUp: function () {
        var input, filter, table, tr, td, i, txtValue;
        input = this.$el.find("#searchBarInput")[0];
        filter = input.value.toUpperCase();
        table = this.$el.find("#category_table")
        tr = table[0].children.category_table_body.children;
        for (i = 0; i < tr.length; i++) {
            td = tr[i].children;
            for (var j = 0; j < td.length; j++) {
                txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                    break;
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    },
});
