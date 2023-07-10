odoo.define('auto_fill.AutoFill', function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var basic_fields = require('web.basic_fields');
    var registry = require('web.field_registry');
    var CharField = require('web.basic_fields').FieldChar;
    var FieldAutoFill = CharField.extend({
        template: 'FieldAutoFill',
        events: _.extend({}, CharField.prototype.events, {
            'keyup': '_onKeyup',
            'click #list_matches': '_onTableRowClicked',
        }),
        /**
         * Render the field in readonly mode.
         */
        _renderReadonly: function () {
            var show_value = this._formatValue(this.value);
            this.$el.text(show_value);
        },
        /**
         * Get the current field value.
         * @returns {string} The field value.
         */
        _getValue: function () {
            var $input = this.$el.find('input');
            return $input.val();
        },
         /**
         * Event handler for the keyup event.
         * Performs AJAX request to retrieve matching records based on the input value.
         */
        _onKeyup: function (ev) {
            var value = ev.target.value;
            var self = this;
            ajax.jsonRpc('/matching/records', 'call', {
                model: this.model,
                field: this.name,
                value: value,
            }).then(function (result){
                if (result.length > 0){
                    self.el.lastElementChild.style.display = 'block'
                    var table = self.el.lastElementChild.children[0];
                    $(table).find('tr').remove();
                    var i;
                    for (i = 0; i < result.length; i++) {
                        var row = table.insertRow(i);
                        var cell = row.insertCell(0);
                        cell.innerHTML = result[i];
                    }
                }
                else {
                    self.el.lastElementChild.style.display = 'none'
                }
            }) ;
        },
        /**
         * Event handler for clicking on a table row.
         * Updates the input field value with the clicked row's content.
         *
         * @param {Event} ev - The click event.
         */
        _onTableRowClicked: function (ev) {
            this.el.firstElementChild.firstElementChild.value = ev.target.textContent;
            this.el.lastElementChild.style.display = 'none'
        },
    });
    registry.add('auto_fill', FieldAutoFill);
    return {
        FieldAutoFill: FieldAutoFill,
    };
});