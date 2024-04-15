odoo.define('odoo_screen_recording.VideoWidget', function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var _t = core._t;
    var VideoWidget = AbstractField.extend({
        template: 'VideoWidget',
        supportedFieldTypes: ['char'],
        _render: function () {
            this._super.apply(this, arguments);
            this.$el.find('video').attr('src', this.value);
        },
    });
    field_registry.add('videoWidget', VideoWidget);
});
