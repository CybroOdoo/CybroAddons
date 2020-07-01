odoo.define('pos_traceability_validation.models', function (require) {
"use strict";

    var PosModel = require('point_of_sale.models');
    var PosPopups = require('point_of_sale.popups');
    var gui = require('point_of_sale.gui');
    var rpc = require('web.rpc');
    var PackLotLinePopupWidget = PosPopups.extend({
        template: 'PackLotLinePopupWidget',
         events: _.extend({}, PosPopups.prototype.events, {
        'click .remove-lot': 'remove_lot',
        'keydown': 'add_lot',
        'blur .packlot-line-input': 'lose_input_focus',
    }),

        /*making sure we didn't used same key already in the order*/
        duplicate_lot_name: function(id, lot_name, lot_lines){
            for(var i=0; i< lot_lines.length; i++){
                if(lot_lines[i].attributes &&
                    lot_lines[i].attributes.lot_name != null
                    && lot_lines[i].attributes.lot_name == lot_name &&
                    id != lot_lines[i].cid){
                    return true;
                }
            }
            return false;
        },

        click_confirm: function(){
            var self = this;
            var lot_names = [];
            var lot_cid = {};
            var pack_lot_lines = this.options.pack_lot_lines;

            this.$('.packlot-line-input').each(function(index, el){
                var cid = $(el).attr('cid'),
                    lot_name = $(el).val();
                var pack_line = pack_lot_lines.get({cid: cid});
                pack_line.set_lot_name(lot_name);
                lot_names.push(lot_name);
                lot_cid[lot_name] = cid;
            });

            rpc.query({
                model: 'serial_no.validation',
                method: 'validate_lots',
                args: [lot_names]
                }).then(function(result){

                if(result != true){
                    var current_id = lot_cid[result[1]];
                    var pack_line = pack_lot_lines.get({cid: current_id});
                    pack_line.set_lot_name(null);
                    if(result[0] == 'no_stock'){
                        alert("Insufficient stock for " + result[1])
                    }
                    else if(result[0] == 'duplicate'){
                        alert("Duplicate entry for " + result[1])
                    }
                    else if(result[0] == 'except'){
                        alert("Exception occured with " + result[1])
                    }
                }
                else{
                    pack_lot_lines.set_quantity_by_lot();
                    self.options.order.save_to_db();
                    self.options.order_line.trigger(
                        'change',
                        self.options.order_line
                    );
                    self.gui.close_popup();
                }
            });
        },
        add_lot: function(ev) {
        if (ev.keyCode === $.ui.keyCode.ENTER && this.options.order_line.product.tracking == 'serial') {
          var pack_lot_lines = this.options.pack_lot_lines,
            $input = $(ev.target),
            cid = $input.attr('cid'),
            lot_name = $input.val();
          var lot_model = pack_lot_lines.get({ cid: cid });
          lot_model.set_lot_name(lot_name); // First set current model then add new one
          if (!pack_lot_lines.get_empty_model()) {
            var new_lot_model = lot_model.add();
            this.focus_model = new_lot_model;
          }
          pack_lot_lines.set_quantity_by_lot();
          this.renderElement();
          this.focus();
        }
      },
        remove_lot: function(ev){
        var pack_lot_lines = this.options.pack_lot_lines,
            $input = $(ev.target).prev(),
            cid = $input.attr('cid');
        var lot_model = pack_lot_lines.get({cid: cid});
        lot_model.remove();
        pack_lot_lines.set_quantity_by_lot();
        this.renderElement();
    },
    lose_input_focus: function(ev) {
        var $input = $(ev.target),
          cid = $input.attr('cid');
        var lot_model = this.options.pack_lot_lines.get({ cid: cid });
        lot_model.set_lot_name($input.val());
      },
      focus: function() {
        this.$("input[autofocus]").focus();
        this.focus_model = false;
      },
    });
    gui.define_popup({name:'packlotline', widget: PackLotLinePopupWidget});

});



