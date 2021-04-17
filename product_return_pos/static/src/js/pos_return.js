odoo.define('product_return_pos.pos_return',function(require) {
    "use strict";


var models = require('point_of_sale.models');


var gui = require('point_of_sale.Gui');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var _t  = require('web.core')._t;
var session = require('web.session');
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
    const { useState, useRef ,useSubEnv} = owl.hooks;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const OrderManagementScreen = require('point_of_sale.OrderManagementScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');



class ReturnWidget extends AbstractAwaitablePopup {
    constructor() {
            super(...arguments);
            this.state = useState({ inputValue: this.props.startingValue });
            this.inputRef = useRef('input');
            useSubEnv({ attribute_components: [] });

        }
    mounted() {
        this.render_list()
    }

    render_list(){
        $("#table-body").empty();
        var lines = [];
       var pos_reference = this.props.ref
        rpc.query({
                model: 'pos.order',
                method: 'get_lines',
                args: [pos_reference],
            }).then(function (result) {
                lines = result[0];
                for(var j=0;j < lines.length; j++){
                    var product_line = lines[j];
                    var rows = "";
                    var id = product_line.product_id
                    var price_unit = product_line.price_unit;
                    var name =product_line.product;
                    var qty = product_line.qty;
                    var line_id = product_line.line_id;
                    var discount = product_line.discount;
                    rows += "<tr><td>" + id + "</td><td>" + price_unit +" </td><td>" + name + "</td><td>" + qty + "</td><td>" + discount + "</td><td>" + line_id + "</td></tr>";
                    $(rows).appendTo("#list tbody");
                    var rows = document.getElementById('list').rows;
                    for (var row = 0; row < rows.length; row++) {
                        var cols = rows[row].cells;
                        cols[0].style.display = 'none';
                        cols[1].style.display = 'none';
                        cols[5].style.display = 'none';

                    }

                }
                var table = document.getElementById('list');
                var tr = table.getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {
                  var td = document.createElement('td');
                  var input = document.createElement('input');
                  input.setAttribute("type", "text");
                  input.setAttribute("value", 0);
                  input.setAttribute("id", "text"+i);
                  td.appendChild(input);
                  tr[i].appendChild(td);

                }
            }).catch(function () {
                alert("NO DATA")
            });
    }



    click_confirm() {

        var self = this;
	    var myTable = document.getElementById('list').tBodies[0];
        var count  = 0;
        var c = 1;

        for (r=0, n = myTable.rows.length; r < n; r++) {
            var row = myTable.rows[r]
            var return_qty = document.getElementById("text"+c).value
            if (row.cells[3].innerHTML < return_qty){
                count +=1
            }
            c = c+1
        }
        if (count > 0){
             alert('Please check the Returned Quantity,it is higher than purchased')
        }
        else{
            c = 1;
            // OrderSuper.prototype.set_client.call(this, this.client);
            for (var r=0, n = myTable.rows.length; r < n; r++) {
                row = myTable.rows[r]
                return_qty = document.getElementById("text"+c).value;
                var product   = this.env.pos.db.get_product_by_id(row.cells[0].innerHTML);
                if (!product) {
                    return;
                }

                if (return_qty > 0){
                    this.env.pos.get_order().add_product(product, {
                    price: row.cells[1].innerHTML,
                    quantity: -(return_qty),
                    discount:row.cells[4].innerHTML,
                    merge: false,
                    extras: {return_ref: this.props.ref,
                            label:row.cells[5].innerHTML},
                    });

                }
                c = c+1

            }

            if (this.props.client){
                    this.env.pos.get_order().set_client(this.env.pos.db.get_partner_by_id(this.props.client));
            }

        }
        this.trigger('close-popup');
        this.showScreen('ProductScreen')

    }

    }
    ReturnWidget.template = 'ReturnWidget';
    ReturnWidget.defaultProps = {
        confirmText: 'Return',
        cancelText: 'Cancel',
        title: 'Confirm ?',
        body: '',
    };

    Registries.Component.add(ReturnWidget);

    return ReturnWidget;



});