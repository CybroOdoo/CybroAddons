odoo.define('auto_fill.AutoFill', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var basic_fields = require('web.basic_fields');
    var registry = require('web.field_registry');
    var CharField = registry.get('char');

    var FieldAutoFill = CharField.extend({
        template: 'FieldAutoFill',
        events: _.extend({}, CharField.prototype.events, {
            'keyup': '_onKeyup',
            'click #list_matches': '_onTableRowClicked',
        }),

        _onKeyup: function () {
            var value = document.getElementsByClassName('input_field_auto_fill')[0].value;
            ajax.jsonRpc('/matching/records', 'call', {
                model: this.model,
                field: this.name,
                value: value,
            }).then(function (result){
                if (result.length > 0){
                    $('.auto-fill-scrollbar').css('display', 'block');
                    var table = document.getElementById("list_matches");
                    $("#list_matches tr").remove();
                    var i;
                    for (i = 0; i < result.length; i++) {
                        var row = table.insertRow(i);
                        var cell = row.insertCell(0);
                        cell.innerHTML = result[i];
                    }
                }
                else {
                    $('.auto-fill-scrollbar').css('display', 'none');
                }
            }) ;
        },

        _onTableRowClicked: function (ev) {
            document.getElementsByClassName('input_field_auto_fill')[0].value = ev.target.textContent;
            $('.auto-fill-scrollbar').css('display', 'none');
        },
        
    });
    
    registry.add('auto_fill', FieldAutoFill);

    return {
        FieldAutoFill: FieldAutoFill,
    };

});
