odoo.define('product_return_pos.order_list_screen',function(require) {
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
    const { useState , useRef} = owl.hooks;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');
    const { posbus } = require('point_of_sale.utils');
    const { Gui } = require('point_of_sale.Gui');


    class OrderListScreenWidget extends IndependentToOrderScreen {
         constructor() {
            super(...arguments);
            useListener('filter-selected', this._onFilterSelected);
            useListener('search', this._onSearch);
            this.searchDetails = {};
            this.filter = null;
            this._initializeSearchFieldConstants();
         }

        mounted() {
            var self = this;
            this.render();
            var orders = this.env.pos.orders;
            var search_timeout = null;
        }
        back() {
            this.close();
        }
        reload(){
            window.location.reload();
        }

        return_click(order){
            this.return_order(order);
        }
        get ordersList() {
                const filterCheck = (order) => {
                    return true;
                };
                const { fieldName, searchTerm } = this.searchDetails;
                const searchField = this._searchFields[fieldName];
                const searchCheck = (order) => {
                    if (!searchField) return true;
                    const repr = searchField.repr(order);
                    if (repr === null) return true;
                    if (!searchTerm) return true;
                    return repr && repr.toString().toLowerCase().includes(searchTerm.toLowerCase());
                };
                const predicate = (order) => {
                    return filterCheck(order) && searchCheck(order);
                };

                return this.orderList.filter(predicate);
        }
        _onFilterSelected(event) {
                this.filter = event.detail.filter;
                this.render();
            }
        get orderList() {
                return this.env.pos.orders;
            }
        get _searchFields() {
            const fields = {

                        RECEIPT_NUMBER: {
                            repr: (order) => order.name,
                            displayName: this.env._t('Receipt Number'),
                            modelField: 'pos_reference',
                        },

                        DATE: {
                            repr: (order) => order.date_order,
                            displayName: this.env._t('Date'),
                            modelField: 'date_order',
                        },
                        CUSTOMER: {
                            repr: (order) => order.partner_id[1],
                            displayName: this.env._t('Customer'),
                            modelField: 'partner_id.display_name',
                        },
                         RETURN_REF: {
                            repr: (order) => order.return_ref,
                            displayName: this.env._t('Return Ref'),
                            modelField: 'return_ref',
                        },

                    };
                    return fields;
                }
        _onSearch(event) {
                const searchDetails = event.detail;
                Object.assign(this.searchDetails, searchDetails);
                this.render();
            }
        get searchBarConfig() {
                return {
                    searchFields: new Map(
                        Object.entries(this._searchFields).map(([key, val]) => [key, val.displayName])
                    ),
                    filter: { show: true, options: this.filterOptions },
                    defaultSearchDetails: this.searchDetails,
                };
            }
        get filterOptions() {
              const orderStates = this._getOrderStates();
                return orderStates;
            }
        _getOrderStates() {
                const states = new Map();
                states.set('All Orders', {
                    text: this.env._t('All Orders'),
                });
                return states;
            }
        getStatus(order) {
               const screen = order.get_screen_data();
               return this._getOrderStates().get(this.__screenToStatusMap[screen.name]).text;

            }
        get _screenToStatusMap() {
                return {
                    ProductScreen: 'Ongoing',
                    PaymentScreen: 'Payment',
                    ReceiptScreen: 'Receipt',
                };
            }

        _initializeSearchFieldConstants() {
                this.constants = {};
                Object.assign(this.constants, {
                    searchFieldNames: Object.keys(this._searchFields),
                    screenToStatusMap: this._screenToStatusMap,
                });
            }

        render_list(orders){
            var contents = this.el.querySelector('.order-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(orders.length,1000); i < len; i++){
                var order    = orders[i];
                var orderline_html = this.env.qweb.render('OrderLine',{widget: this, order:order});
                var orderline = document.createElement('tbody');
                orderline.innerHTML = orderline_html;
                orderline = orderline.childNodes[1];
                contents.appendChild(orderline);
            }
        }

        return_order(order_id){
            var self = this;
            var client = ''
            if (order_id.partner_id){
                 client = order_id.partner_id[0];
            }
            if (order_id && order_id.return_status ==='fully_return'){
                      Gui.showPopup('ErrorPopup',{
                'title': "ERROR",
                'body': "This is a fully returned order",});
            }
            else if (order_id && order_id.return_ref) {

            Gui.showPopup('ErrorPopup',{
                'title': "ERROR",
                'body': "This is a returned order",});
            }
            else{
                Gui.showPopup('ReturnWidget',{ref: order_id.pos_reference,client:client});

            }

        }


    }
        OrderListScreenWidget.template = 'OrderListScreenWidget';

        Registries.Component.add(OrderListScreenWidget);

        return OrderListScreenWidget;

});