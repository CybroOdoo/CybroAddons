/** @odoo-module **/
import basicFields from 'web.basic_fields';
import fieldRegistry from 'web.field_registry';
/**
     * Custom field widget for time selection.
     * Extends the basic input field provided by Odoo.
 */
var FieldTimePicker = basicFields.InputField.extend({
    /**
        * Template used for rendering the time picker field.
     */
    template: 'FieldTimePicker',
    /**
         * Events associated with the time picker field, extending the base events.
         * Adds a blur event for the time input element.
         * @type {Object}
     */
    events:_.extend({}, basicFields.InputField.prototype.events, {
       'blur .time-input' : '_onBlur',
    }),
    /**
         * Get the current value of the time picker field.
         * @returns {string} - The value of the time picker input.
         * @private
     */
    _getValue: function () {
        var $input = this.$el.find('input');
        return $input.val();
    },
    /**
         * Handle the blur event on the time picker input.
         * Update the internal value of the field when blurred.
         * @param {Event} ev - The blur event.
         * @private
     */
    _onBlur: function(ev) {
         this.value = ev.target.value
    }
});
// Register the custom time picker field in the Odoo field registry.
fieldRegistry.add('timepicker_time', FieldTimePicker);
return {
    FieldTimePicker: FieldTimePicker
};
