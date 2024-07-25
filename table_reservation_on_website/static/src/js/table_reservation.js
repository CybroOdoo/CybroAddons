/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
publicWidget.registry.table_reservation = publicWidget.Widget.extend({
    selector: '.swa_container',
    events: {
        'change #floors_rest': '_onFloorChange',
    },
    /**
    To get all tables belongs to the floor
    **/
    _onFloorChange: function (ev) {
        var floors = this.$el.find("#floors_rest")[0].value;
        var date = this.$el.find("#date_booking").text().trim()
        var start = this.$el.find("#booking_start").text()
        if (document.getElementById('count_table')){
            document.getElementById('count_table').innerText = 0;
        }
        if (document.getElementById('total_amount')){
            document.getElementById('total_amount').innerText = 0;
        }
        var self = this
        if (floors && date && start) {
            jsonrpc("/restaurant/floors/tables", {'floors_id' : floors,
            'date': date, 'start':start,})
            .then(function (data) {
                if(floors == 0){
                    self.$el.find('#table_container_row').empty();
                    self.$el.find('#info').hide();
                }
                else{
                    self.$el.find('#table_container_row').empty();
                    self.$el.find('#info').show();
                    for (let i in data){
                        if (Object.keys(data).length > 1) {
                            let amount = '';
                            if (data[i]['rate'] != 0) {
                                amount = '<br/><span><i class="fa fa-money"></i></span><span id="rate">' + data[i]['rate'] + '</span>/Slot';
                            }
                            self.$el.find('#table_container_row').append('<div id="'+data[i]['id'] +
                            '" class="card card_table col-sm-2" style="background-color:#96ccd5;padding:0;margin:5px;width:250px;"><div class="card-body"><b>'  +data[i]['name'] +
                            '</b><br/><br/><br/><span><i class="fa fa-user-o" aria-hidden="true"></i> '+ data[i]['seats']+
                            '</span>' + amount + '</div></div><br/>');
                        }
                        else {
                            let amount = '';
                            if (data[i]['rate'] != 0) {
                                amount = '<br/><span><i class="fa fa-money"></i></span><span id="rate">' + data[i]['rate'] + '</span>/Slot';
                            }
                            self.$el.find('#table_container_row').append('<div id="'+data[i]['id'] +
                            '" class="card card_table col-sm-2" style="background-color:#96ccd5;padding:0;margin:15px;width:250px;"><div class="card-body"><b>'  +data[i]['name'] +
                            '</b><br/><br/><br/><span><i class="fa fa-user-o" aria-hidden="true"></i> '+ data[i]['seats']+
                            '</span>' + amount + '</div></div><br/>');
                        }
                    }
                }
            });
        }
    },
});
