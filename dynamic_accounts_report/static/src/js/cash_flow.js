odoo.define('dynamic_cash_flow_statements.cash_flow', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var _t = core._t;

    window.click_num = 0;
    var CashFlow = AbstractAction.extend({
    template: 'CFTemp',
        events: {
            'click .parent-line': 'journal_line_click',
            'click .child_col1': 'journal_line_click',
            'click #apply_filter': 'apply_filter',
            'click #pdf': 'print_pdf',
            'click #xlsx': 'print_xlsx',
            'click .cf-line': 'get_move_lines',
        },

        init: function(parent, action) {
        this._super(parent, action);
                this.currency=action.currency;
                this.report_lines = action.report_lines;
                this.wizard_id = action.context.wizard | null;
            },


          start: function() {
            var self = this;
            self.initial_render = true;
            rpc.query({
                model: 'account.cash.flow',
                method: 'create',
                args: [{

                }]
            }).then(function(t_res) {
                self.wizard_id = t_res;
                self.load_data(self.initial_render);
            })
        },

        get_move_lines: function(event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
            self._rpc({
                model: 'account.cash.flow',
                method: 'view_report',
                args: [
                    [self.wizard_id]
                ],
            }).then(function(datas) {

                    if(datas['levels']== 'detailed'){
                        $(event.currentTarget).next('tr').find('td ul').after(
                            QWeb.render('SubSectionCF', {
                                count: 3,
                                offset: 0,
                                account_data: datas['journal_res'],
                                level:datas['levels'],
                                currency : datas['currency'],
                                line_id:parseInt(event.currentTarget.attributes[3].value),
                            }))
                    }else if(datas['levels']== 'very'  || datas['levels']== false){
                            $(event.currentTarget).next('tr').find('td ul').after(
                            QWeb.render('ChildSubSectionCF', {
                                count: 3,
                                offset: 0,
                                account_data: datas['account_res'],
                                level:datas['levels'],
                                currency : datas['currency'],
                                line_id:parseInt(event.currentTarget.attributes[3].value),
                            }))
                    }

                    $(event.currentTarget).next('tr').find('td ul li:first a').css({
                        'background-color': '#00ede8',
                        'font-weight': 'bold',
                    });
                })
            }
        },


        load_data: function (initial_render = true) {
            var self = this;
                self.$(".categ").empty();
                try{
                    var self = this;
                    self._rpc({
                        model: 'account.cash.flow',
                        method: 'view_report',
                        args: [[this.wizard_id]],
                    }).then(function(datas) {
                            if (initial_render) {
                                    self.$('.filter_view_tb').html(QWeb.render('CashFilterView', {
                                        filter_data: datas['filters'],
                                    }));
                                    self.$el.find('.journals').select2({
                                        placeholder: 'Select Journals...',
                                    });
                            }
                            var child=[];

                        self.$('.table_view_tb').html(QWeb.render('CashTable', {

                                            account_data: datas['fetched_data'],
                                            level:datas['levels'],
                                            currency : datas['currency'],
                                        }));

                });

                    }
                catch (el) {
                    window.location.href
                    }
            },

            show_gl: function(e) {
            var self = this;
            var account_id = $(e.target).attr('data-account-id');
            var options = {
                account_ids: [account_id],
            }

                var action = {
                    type: 'ir.actions.client',
                    name: 'GL View',
                    tag: 'g_l',
                    target: 'new',

                    domain: [['account_ids','=', account_id]],


                }
                return this.do_action(action);

        },
            print_pdf: function(e) {
            e.preventDefault();
            var self = this;
            self._rpc({
                model: 'account.cash.flow',
                method: 'view_report',
                args: [
                    [self.wizard_id]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'dynamic_accounts_report.cash_flow',
                    'report_file': 'dynamic_accounts_report.cash_flow',
                    'data': {
                        'report_data': data
                    },
                    'context': {
                        'active_model': 'account.cash.flow',
                        'landscape': 1,
                        'trial_pdf_report': true
                    },
                    'display_name': 'Cash Flow Statements',
                };
                return self.do_action(action);
            });
        },



        print_xlsx: function() {
            var self = this;
            self._rpc({
                model: 'account.cash.flow',
                method: 'view_report',
                args: [
                    [self.wizard_id]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir_actions_dynamic_xlsx_download',
                    'data': {
                         'model': 'account.cash.flow',
                         'options': JSON.stringify(data['filters']),
                         'output_format': 'xlsx',
                         'report_data': JSON.stringify(data['report_lines']),
                         'report_name': 'Cash Flow Statements',
                         'dfr_data': JSON.stringify(data),
                    },
                };
                return self.do_action(action);
            });
        },

        journal_line_click: function (el){
            click_num++;
            var self = this;
            var line = $(el.target).parent().data('id');
            return self.do_action({
                type: 'ir.actions.act_window',
                    view_type: 'form',
                    view_mode: 'form',
                    res_model: 'account.move',
                    views: [
                        [false, 'form']
                    ],
                    res_id: line,
                    target: 'current',
            });

        },


        apply_filter: function(event) {

            event.preventDefault();
            var self = this;
            self.initial_render = false;

            var filter_data_selected = {};



            if ($(".levels").length){
            var level_res = document.getElementById("level_res")
            filter_data_selected.levels = $(".levels")[0].value
            level_res.value = $(".levels")[0].value
            level_res.innerHTML=level_res.value;
            if ($(".levels").value==""){
            type_res.innerHTML="summary";
            filter_data_selected.type = "Summary"
            }
            }

            if ($("#date_from").val()) {
                var dateString = $("#date_from").val();
                filter_data_selected.date_from = dateString;
            }
            if ($("#date_to").val()) {
                var dateString = $("#date_to").val();
                filter_data_selected.date_to = dateString;
            }

            if ($(".target_move").length) {
            var post_res = document.getElementById("post_res")
            filter_data_selected.target_move = $(".target_move")[0].value
            post_res.value = $(".target_move")[0].value
                    post_res.innerHTML=post_res.value;
              if ($(".target_move")[0].value == "") {
              post_res.innerHTML="posted";

              }
            }
            rpc.query({
                model: 'account.cash.flow',
                method: 'write',
                args: [
                    self.wizard_id, filter_data_selected
                ],
            }).then(function(res) {
            self.initial_render = false;
                self.load_data(self.initial_render);
            });
        },

    });
    core.action_registry.add("c_f", CashFlow);
    return CashFlow;
});