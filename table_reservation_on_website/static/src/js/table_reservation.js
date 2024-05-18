/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
publicWidget.registry.table_reservation = publicWidget.Widget.extend({
    selector: '#restaurant_floors',
    events: {
        'change #floors_rest': '_onFloorChange',
        'click .card_table': '_onTableClick',
    },
    /**
    To get all tables belongs to the floor
    **/
    _onFloorChange: function (ev) {
        var floors = this.$el.find("#floors_rest")[0].value;
        var date = $("#date_booking").text().trim()
        var start = $("#booking_start").text()
        document.getElementById('count_table').innerText = 0;
        document.getElementById('total_amount').innerText = 0;
        jsonrpc("/restaurant/floors/tables", {'floors_id' : floors,
        'date': date, 'start':start,})
        .then(function (data) {
            if(floors == 0){
                $('#table_container_row').empty();
                $('#info').hide();
            }
            else{
                $('#table_container_row').empty();
                $('#info').show();
                for (let i in data){
                   $('#table_container_row').append('<div id="'+data[i]['id'] +
                   '" class="card card_table col-sm-2" style="background-color:#96ccd5;padding:0;margin:5px;width:250px;"><div class="card-body"><b>'  +data[i]['name'] +
                    '</b><br/><br/><br/><span><i class="fa fa-user-o" aria-hidden="true"></i> '+ data[i]['seats']+
                    '</span><br/><span><i class="fa fa-money"></i></span><span id="rate">'
                    + data[i]['rate'] +
                    '</span>/Slot</div></div><br/>');
                }
            }
        });
    },
});
