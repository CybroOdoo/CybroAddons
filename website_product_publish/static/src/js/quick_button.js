odoo.define('website_product_publish.quick_.button', function (require) {
'use strict';

var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');

var _t = core._t;

// Creating a new button widget for 'Quick Publish' which works same as the current publish button widget.

var QuickWebsitePublishButton = AbstractField.extend({
    template: 'QuickWebsitePublishButton',
    events: {
        'click': '_onClick',
    },

    start: function () {
        this.$icon = this.$('.o_button_icon');
        return this._super.apply(this, arguments);
    },

    isSet: function () {
        return true;
    },

    _render: function () {
        this._super.apply(this, arguments);

        var published = this.value;
        var info = published ? _t("Published") : _t("Unpublished");
        this.$el.attr('aria-label', info)
                .prop('title', info);
        this.$icon.toggleClass('text-danger', !published)
                .toggleClass('text-success', published);
    },

    _onClick: function () {
        var self = this;
        this._rpc({
            model: this.model,
            method: 'quick_publish_products',
            args: [this.res_id],
        }).then(function (result) {
            self.do_action(result);
        });
    },
});

field_registry
    .add('quick_publish_button', QuickWebsitePublishButton)
});
