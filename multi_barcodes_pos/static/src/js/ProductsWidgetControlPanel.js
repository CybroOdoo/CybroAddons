odoo.define('multi_barcodes_pos.barcode_search_db', function(require) {
    "use strict";

var PosDB = require('point_of_sale.DB');

PosDB.include({

_product_search_string: function(product) {
    var result = product.pos.product_barcodes.filter(function(dataObj){
       return dataObj.product_multi[0] === product.id
    })
    var str = product.display_name;
    if (product.barcode) {
        str += '|' + product.barcode;
    }
    if (product.default_code) {
        str += '|' + product.default_code;
    }
    if (product.description) {
        str += '|' + product.description;
    }
    if (product.description_sale) {
        str += '|' + product.description_sale;
    }
    if (product.barcode_carton) {
        str += '|' + product.barcode_carton;
    }
    if (result.length !=0) {
    result.forEach(item =>   str += '|' + item.multi_barcode);
    }
    str = product.id + ':' + str.replace(/:/g, '') + '\n';
    return str;
},

});
    });