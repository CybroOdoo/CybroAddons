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
            var show_value = this._formatValue(this.value);
            this.$el.find('input')[0].value=show_value;
            var self = this;
            this.$el.on('click', '.timepickerg', function() {
                self._onClickTimePicker();
            });
        },
        _onClickTimePicker: function() {
            /**
             * Function to be executed when the "timepickerg" class is clicked.
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

odoo.define('field_timepicker.time_picker_add_exception', function(require) {
    "use_strict";

    var BasicModel = require('web.BasicModel');

    BasicModel.include({
         /**
         * Override the applyChange method of BasicModel.
         *
         */
        _applyChange: function(recordID, changes, options) {
            var self = this;
            var record = this.localData[recordID];
            var field;
            var defs = [];
            options = options || {};
            record._changes = record._changes || {};
            if (!options.doNotSetDirty) {
                record._isDirty = true;
            }
            var initialData = {};
            this._visitChildren(record, function(elem) {
                initialData[elem.id] = $.extend(true, {}, _.pick(elem, 'data', '_changes'));
            });
            // apply changes to local data
            for (var fieldName in changes) {
                field = record.fields[fieldName];
                if (field.type === 'one2many' || field.type === 'many2many') {
                    defs.push(this._applyX2ManyChange(record, fieldName, changes[fieldName], options.viewType));
                } else if (field.type === 'many2one' || field.type === 'reference') {
                    defs.push(this._applyX2OneChange(record, fieldName, changes[fieldName]));
                } else {
                    record._changes[fieldName] = changes[fieldName];
                }
            }
            if (options.notifyChange === false) {
                return $.Deferred().resolve(_.keys(changes));
            }
            return $.when.apply($, defs).then(function() {
                var onChangeFields = []; // the fields that have changed and that have an on_change
                for (var fieldName in changes) {
                    field = record.fields[fieldName];
                    if (field.onChange) {
                        var isX2Many = field.type === 'one2many' || field.type === 'many2many';
                        if (!isX2Many || (self._isX2ManyValid(record._changes[fieldName] || record.data[fieldName]))) {
                            onChangeFields.push(fieldName);
                        }
                    }
                }
                var onchangeDef = $.Deferred();
                if (onChangeFields.length) {
                    self._performOnChange(record, onChangeFields, options.viewType)
                        .then(function(result) {
                            delete record._warning;
                            onchangeDef.resolve(_.keys(changes).concat(Object.keys(result && result.value || {})));
                        }).fail(function() {
                            self._visitChildren(record, function(elem) {
                                _.extend(elem, initialData[elem.id]);
                            });
                            onchangeDef.resolve({});
                        });
                } else {
                    onchangeDef = $.Deferred().resolve(_.keys(changes));
                }
                return onchangeDef.then(function(fieldNames) {
                    _.each(fieldNames, function(name) {
                        var excpet = {};
                        if (record && record['fieldsInfo'] && record['fieldsInfo']['form'] && record['fieldsInfo']['form'][name]) {
                            var curr_el = record['fieldsInfo']['form'][name];
                            if (curr_el['widget'] == 'timepicker') {
                                excpet[name] = true;
                            }
                        }
                        if (record._changes && record._changes[name] === record.data[name]) {
                            delete record._changes[name];
                            record._isDirty = !_.isEmpty(record._changes);
                        } else if (record._changes && record._changes[name] != record.data[name]) {
                            if (excpet[name] && excpet[name] == true) {
                                //delete record._changes[name];
                                fieldNames.splice(fieldNames.indexOf(name), 1);
                                record._isDirty = !_.isEmpty(fieldNames);
                            }
                        }
                    });
                    return self._fetchSpecialData(record).then(function(fieldNames2) {
                        // Return the names of the fields that changed (onchange or
                        // associated special data change)
                        return _.union(fieldNames, fieldNames2);
                    });
                });
            });
        }
    });
});