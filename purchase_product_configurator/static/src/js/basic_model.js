odoo.define('purchase_product_configurator.BasicModel', function (require) {
'use strict';

var BasicModel = require('web.BasicModel');
const { patch, unpatch } = require('web.utils');


patch(BasicModel.prototype, 'purchase_product_configurator/static/src/js/basic_model.js', {

    /**
    * Patch the _applyChange method of the BasicModel to handle specific field changes.
    */
    _applyChange (recordID, changes, options) {
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
        this._visitChildren(record, function (elem) {
            initialData[elem.id] = $.extend(true, {}, _.pick(elem, 'data', '_changes'));
        });
        // apply changes to local data
        for (var fieldName in changes) {
            field = record.fields[fieldName];

            if (field && (field.type === 'one2many' || field.type === 'many2many')) {
                if (fieldName == "product_custom_attribute_value_ids") {
                continue
                };
                defs.push(this._applyX2ManyChange(record, fieldName, changes[fieldName], options));
            } else if (field && (field.type === 'many2one' || field.type === 'reference')) {
                defs.push(this._applyX2OneChange(record, fieldName, changes[fieldName], options));
            } else {
                record._changes[fieldName] = changes[fieldName];
            }
        }
        if (options.notifyChange === false) {
            return Promise.all(defs).then(function () {
                return Promise.resolve(_.keys(changes));
            });
        }
        return Promise.all(defs).then(function () {
            var onChangeFields = []; // the fields that have changed and that have an on_change

            for (var fieldName in changes) {
                field = record.fields[fieldName];
                if (field && field.onChange) {
                    var isX2Many = field.type === 'one2many' || field.type === 'many2many';
                    if (!isX2Many || (self._isX2ManyValid(record._changes[fieldName] || record.data[fieldName]))) {
                        onChangeFields.push(fieldName);
                    }
                }
            }
            return new Promise(function (resolve, reject) {
                if (onChangeFields.length) {
                    self._performOnChange(record, onChangeFields, { viewType: options.viewType })
                    .then(function (result) {
                        delete record._warning;
                        resolve(_.keys(changes).concat(Object.keys(result && result.value || {})));
                    }).guardedCatch(function () {
                        self._visitChildren(record, function (elem) {
                            _.extend(elem, initialData[elem.id]);
                        });
                        reject();
                    });
                } else {
                    resolve(_.keys(changes));
                }
            }).then(function (fieldNames) {
                return self._fetchSpecialData(record).then(function (fieldNames2) {
                    // Return the names of the fields that changed (onchange or
                    // associated special data change)
                    return _.union(fieldNames, fieldNames2);
                });
            });
        });
    },
  })
})