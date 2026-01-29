odoo.define('pos_night_mode.pos_chrome', function (require) {
    'use strict';
//    Extending Chrom component
    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const PosNightMod = (Chrome) =>
        class extends Chrome {
            async start() {
                this.night_mode = 'True'
                var self = this;
                await super.start();
                rpc.query({
                    model: 'res.users',
                    method: 'get_active'
                }).then(function(res){
                    if(res){
                        self._OnNightTrue()
                    }
                })
            };
//            Clicking sun icon
            OnClickSun(){
                var self = this;
                rpc.query({
                    model: 'res.users',
                    method: 'set_deactivate'
                }).then(function(){
                    $('style').remove()
                })
                $("#fa-icon").addClass("d-none")
                $("#fa-icon-moon").removeClass("d-none")
            };
//            Clicking moon icon
            OnClickMoon() {
                var self = this;
                rpc.query({
                    model:'res.users',
                    method: 'set_active'
                }).then(function(){
                    self._OnNightTrue()
                })
                 $("#fa-icon").removeClass("d-none")
                 $("#fa-icon-moon").addClass("d-none")
            };
//            Making nightmode in POS
            async _OnNightTrue(){ //Added a function for click button change the pos color to black
                var pos_element = document.querySelector('.pos')
                var pos_product_list_modifier = document.createElement('style')
                pos_product_list_modifier.innerHTML = '.pos{color:white;}'+'.pos .product { background-color:#3c3f41 !important;border:'+
                'thin solid white;border-radius: 5px;}.pos .product .product-img img {background-image:'+
                'linear-gradient(to bottom,white,#3c3f41) !important;}'+
                '.pos .product-list-container{background-color:#3c3f41 !important;}'+
                '.pos .product .price-tag {color:#F45976 !important;}'+
                '.pos .product .product-name{color:white}'+
                '.pos .order{background-color:#3c3f41}'+
                '.pos .rightpane{background-color:#3c3f41}'+
                '.pos .rightpane-header{background-color:#3c3f41;}'+
                '.pos .pos-content .product-screen .leftpane .pads .control-buttons .fw-bolder{color:white;}'+
                '.pos .breadcrumb-button{color:white}'+
                '.pos .category-simple-button{background-color:#3c3f41 !important;}'+
                '.pos .sb-product .pos-search-bar{background-color:#3c3f41 !important;}'+
                '.pos .rightpane-header .pos-search-bar input, .pos .clientlist-screen'+
                '.pos-search-bar input{color:#adb7c1}'+
                '.pos .order .orderline .selected{background-color:darkgray !important}'+
                '.pos .order .orderline .info-list{color:#B3B7BF !important}'+
                '.pos .order .orderline .info-list em{color:#B3B7BF !important}'+
                '.pos .control-button{background-color:#3c3f41 !important;}'+
                '.pos .mode-button.selected-mode{background-color:#707375 !important;}'+
                '.pos .numpad button{background-color:#3c3f41;color:white;}'+
                '.pos .numpad button:hover{background-color:#f45976 !important;}'+
                '.pos .button.validation:hover{background-color:#f45976 !important;}'+
                '.pos .actionpad .button{background-color:#3c3f41;color:white;}'+
                '.pos .actionpad .button:hover{background-color:#f45976 !important;}'+
                '.pos .control-button:hover{background-color:#f45976 !important;}'+
                '.pos .modal-dialog .popup{background-color:#1e1f20 !important;}'+
                '.pos .popup .button{background:#8F3536;color: white !important};'+
                '.ticket-screen .controls button {background-color:white;color:black;}'+
                '.ticket-screen .pos-search-bar .filter{color:black}'+
                '.ticket-screen .pos-search-bar .filter .options{border-radius:5px}'+
                '.pos .order-container{background-color:#3c3f41 !important}'+
                '.pos .order-summary{background-color:#3c3f41 !important}'+
                '.pos .order-summary .subentry {color:white !important}'+
                '.pos .pos-content .product-screen .leftpane .pads .control-button .fa-undo{color:white !important}'+
                '.pos .client-window{color:black;}'+
                '.pos .clientlist-screen .client-list thead > tr{background-color:#3c3f41;color:white}'+
                '.pos .clientlist-screen tr.client-line:hover{background-color:#f45976}'+
                '.pos .client-line{color:white;background-color:black !important}'+
                '.pos .clientlist-screen{background-color:black !important}'+
                '.pos .payment-screen{background-color:black !important}'+
                '.pos .receipt-screen{background-color:black !important}'+
                '.pos .screen-content{background-color:black !important}'+
                '.pos .client-list tr.client-line.highlight{background-color:#017e84}'+
                '.screen .screen-content{background-color:#e0e2e6}'+
                '.pos .clientlist-screen .pos-search-bar i{color:black;}'+
                '.pos .clientlist-screen .pos-search-bar input{color:#2a2b2d;}'+
                '.screen .top-content .button.highlight{background-color:#017e84 !important;border-color:#3c3f41 !important;}'+
                '.screen .top-content{background-color:#3c3f41}'+
                '.pos .close-pos-popup header{background-color:rgb(56, 57, 58)}'+
                '.pos .popup .title{background-color:rgb(56, 57, 58)}'+
                '.pos .close-pos-popup .closing-notes{background-color:#c1c3c6}'+
                '.pos .opening-cash-control .opening-cash-notes{background-color:#c1c3c6}'+
                '.payment-screen .main-content{background:#3c3f41}'+
                '.paymentmethods .button{background:#3c3f41}'+
                '.pos .paymentline{background:#3c3f41}'+
                '.pos .paymentline.selected{background:#707375}'+
                '.pos .screen .button.next:not(.highlight){background:#e6e3e2;color:#017e84;}'+
                '.receipt-screen .default-view{background:#3c3f41}'+
                '.receipt-screen .default-view .actions .send-email input{background:#666668;color:white;}'+
                '.receipt-screen .default-view .actions .buttons .button{background:#666668}'+
                '.receipt-screen .default-view .actions .send-email button.send{background:#017e84;color:black}'+
                '.pos .pos-receipt-container > div{color:black}'+
                '.pos .popup.popup-error .button{background:#8F3536}'+
                '.pos .orders .order-row:nth-child(n){background:#3c3f41}'+
                '.pos .orders .order-row.highlight{background:#017e84}'+
                '.pos .orders .order-row:hover{background:#f45976;}'+
                '.pos .pos-content .product-screen .leftpane .bg-100:{background-color:#c1c3c6 !important}'+
                '.payment-screen .payment-buttons .button{background:#3c3f41;color:white;}'+
                '.payment-screen .payment-buttons .button:hover{background:#f45976}'+
                '.modal-title{color:white;}'+
                '.paymentmethod{color:white;}'+
                '.pos-receipt .order-container .orderline {background-color:white;}'+
                '.payment-infos{background-color:#71639e;}'
                ;
                pos_element.parentNode.insertBefore(pos_product_list_modifier, pos_element);
         }
        };
    Registries.Component.extend(Chrome, PosNightMod);
    return Chrome;
});