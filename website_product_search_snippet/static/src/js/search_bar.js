odoo.define('website_product_search_snippet.search', function(require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');


    publicWidget.registry.portalDetails = publicWidget.Widget.extend({
        /**
         *  Retrieve all the data from the table.
         */
        selector: '.product_search_bar',
        events: {
            'keyup .search_product_bar': '_onKeyUp',
        },
        //Function to start a website.
        start: function() {
            this._super.apply(this, arguments);
        },
        //Function to search table datas.
        _onKeyUp: function() {
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
});
