odoo.define('field_timepicker.timepicker', function(require) {
    "use strict";

    var basic_fields = require('web.basic_fields');
    var field_registry = require('web.field_registry');
    var global_show_time = null;
    var FieldChar = require('web.basic_fields').FieldChar;
    var Dialog = require('web.Dialog');

    /**
     * Custom field for time selection.
     */
    var FieldTimePicker = FieldChar.extend({
        template: 'FieldTimePicker',
        widget_class: 'oe_form_field_time',

        /**
         * Renders the field in read-only mode.
         */
        _renderReadonly: function() {
            var show_value = this._formatValue(this.value);
            this.$el.text(show_value);
            global_show_time = show_value;
        },

        /**
         * Gets the current value of the field.
         *
         * @returns {string} The field value.
         */
        _getValue: function() {
            var $input = this.$el.find('input');
            return $input.val();
        },

        /**
         * Renders the field in edit mode.
         */
        _renderEdit: function() {
            this._super.apply(this, arguments);
            var show_value = this._formatValue(this.value);
            this.$el.find('input')[0].value=show_value;
            var self = this;
            this.$el.on('click', '.timepickerg', function() {
                self._onClickTimePicker();
            });
            /**
            * Call the click function.
            */
             setTimeout(function() {
                self._onClickTimePicker();
            }, 50);
        },
        _onClickTimePicker: function() {
            /**
             * Function to be executed when the "timepicker" class is clicked.
             * It renders the field as an editable timepicker widget if the formatType is "char".
             */
            if (this.formatType === "char") {
                var $input = this.$el.find('input');
                var options = {
                    twentyFour: true,
                    title: 'Timepicker',
                    showSeconds: true,
                };
                if (global_show_time) {
                    options['now'] = global_show_time;
                }
                $input.wickedpicker(options);
            } else {
                Dialog.alert(this, "Timepicker widget only works with 'Char' field type");
                return false;
            }
        },
    });

    // Register the FieldTimePicker in the field registry
    field_registry.add('timepicker', FieldTimePicker);

    return {
        FieldTimePicker: FieldTimePicker
    };
});