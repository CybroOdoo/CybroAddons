odoo.define('pivot_heat_map.controllers', function (require) {
    "use strict";

    var PivotController = require('web.PivotController');
    var PivotRenderer = require('web.PivotRenderer');

    PivotController.include({
        init: function (parent, model, renderer, params) {
            renderer.heat_map = null;
            renderer.cells = {};
            this._super(parent, model, renderer, params);
        },
        _onButtonClick: function (event) {
            var $target = $(event.target);
            this._super(event);
            /* catching heat map button click and switching between modes*/
            if ($target.hasClass('o_heat_map_col')) {
                if (this.renderer.heat_map == 'col' ){
                    this.renderer.heat_map = null;
                }
                else{
                    this.renderer.cells = {};
                    this.renderer.heat_map = 'col';
                }

                this.renderer._render();
            }
            else if ($target.hasClass('o_heat_map_row')) {
                if (this.renderer.heat_map == 'row'){
                    this.renderer.heat_map = null;
                }
                else{
                    this.renderer.cells = {};
                    this.renderer.heat_map = 'row';
                }

                this.renderer._render();
            }
            else if ($target.hasClass('o_heat_map_both')) {
                if (this.renderer.heat_map == 'both'){
                    this.renderer.heat_map = null;
                }
                else{
                    this.renderer.cells = {};
                    this.renderer.heat_map = 'both';
                }

                this.renderer._render();
            }
        }
    });
});
