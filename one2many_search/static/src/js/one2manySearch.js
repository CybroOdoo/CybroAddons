odoo.define('one2many_search.search', function (require)
{"use strict";
    var registry = require('web.field_registry');
    var fields = require('web.relational_fields');

    var One2ManySearch = fields.FieldOne2Many.extend({
        template: 'One2ManySearch',
        events: _.extend({}, fields.FieldOne2Many.prototype.events, {
            'keyup .oe_search_value': '_onKeyUp',
        }),

        _onKeyUp: function (event) {
            var self = this;
            self.$el.find('table').addClass('oe_one2many');
            var value = $(event.currentTarget).val().toLowerCase();
            var $el = $(this.$el)
            $(".oe_one2many tr:not(:lt(1))").filter(function() {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
            });
        },

    });
    registry.add('one2many_search', One2ManySearch);
    return {
        One2ManySearch: One2ManySearch,
    };
});