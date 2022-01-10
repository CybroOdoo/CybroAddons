odoo.define('product_multi_uom_pos.multi_uom',function(require) {
"use strict";

console.log("multi_uom_main")

var gui = require('point_of_sale.gui');
var core = require('web.core');
var models = require('point_of_sale.models');
var pos_screens = require('point_of_sale.screens');
var field_utils = require('web.field_utils');
var rpc = require('web.rpc');
var QWeb = core.qweb;
var _t = core._t;
var utils = require('web.utils');
var round_pr = utils.round_precision;

