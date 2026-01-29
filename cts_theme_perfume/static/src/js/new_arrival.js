odoo.define('cts_theme_perfume.new_arrivals', function(require){
'use strict';
var Animation = require('website.content.snippets.animation');
var ajax = require('web.ajax');
var core = require('web.core');

//getting the new arrival product in the website
Animation.registry.arrival_product = Animation.Class.extend({
    xmlDependencies: ['/cts_theme_perfume/static/src/xml/new_arrivals.xml'],
    selector : '.arrivals',
    start: function(){
        var self = this;
        ajax.jsonRpc('/get_arrival_product', 'call', {})
        .then(function (data) {
        console.log(data,'success')
        if(data){
          self.$el.html(core.qweb.render('cts_theme_perfume.new_arrivals_snippet',{
          product_ids: data.product_ids,
          symbol:data.symbol}));
        }
        });
    }
    });
});