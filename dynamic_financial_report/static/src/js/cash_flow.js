odoo.define('dynamic_financial_report.DynamicReports', function(require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var field_utils = require('web.field_utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var _t = core._t;
    var CashFlow = AbstractAction.extend({
        template: 'CashFlow',
        events: {
            'click .cf-line': 'get_move_lines',
            'click .view-move': 'view_move',
            'click #filter_apply_button': 'apply_filter',
            'click #pdf': 'print_pdf',
            'click #xlsx': 'print_xlsx',
        },
        init: function(view, code) {
            this._super(view, code);
            this.wizard = code.context.wizard | null;
            this.session = session;

        },
        start: function() {
            var self = this;
            self.initial_render = true;
            rpc.query({
                model: 'dynamic.cash.flow',
                method: 'create',
                args: [{
                    res_model: this.res_model
                }]
            }).then(function(res) {
                self.wizard = res;
                self.ledger_view(self.initial_render);
            })
        },
        apply_filter: function(event) {
            event.preventDefault();
            var self = this;

            self.initial_render = false;
            var output = {};
            output.reconciled=false;
            output.type=false;
            output.date_from=false;
            output.date_to=false;

            if ($(".level").length){
            var level_res = document.getElementById("level_res")
            output.level = $(".level")[1].value
            level_res.value = $(".level")[1].value
            level_res.innerHTML=level_res.value;
            if ($(".level").value==""){
            type_res.innerHTML="summary";
            output.type = "Summary"
            }
            }


            var journal_ids = [];
            var journal_list = $(".journal").select2('data')
            for (var i = 0; i < journal_list.length; i++) {
                journal_ids.push(parseInt(journal_list[i].id))
            }
            output.journal_ids = journal_ids
            var analytic_ids = [];
            var analytic_list = $(".analytic").select2('data')
            for (var i = 0; i < analytic_list.length; i++) {
                analytic_ids.push(parseInt(analytic_list[i].id))
            }
            output.analytic_ids = analytic_ids
            var analytic_tag_ids = [];
            var analytic_tag_list = $(".analytic-tag").select2('data')
            for (var i = 0; i < analytic_tag_list.length; i++) {
                analytic_tag_ids.push(parseInt(analytic_tag_list[i].id))
            }
            output.analytic_tag_ids = analytic_tag_ids
            if ($(".target-moves").length){
                var target_res = document.getElementById("target_res")
                output.target_moves = $(".target-moves")[1].value
                target_res.value = $(".target-moves")[1].value
                target_res.innerHTML=target_res.value;
                if ($(".target-moves").value==""){
                target_res.innerHTML="all";
                output.target_moves = "all"
                }
            }

            if ($("#date_from").val()) {
                var dateObject = $("#date_from").datepicker("getDate");
                var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
                output.date_from = dateString;
            }

            if ($("#date_to").val()) {
                var dateObject = $("#date_to").datepicker("getDate");
                var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
                output.date_to = dateString;
            }
            output.include_details = true;

            rpc.query({
                model: 'dynamic.cash.flow',
                method: 'write',
                args: [
                    [self.wizard], output
                ],
            }).then(function(res) {
                self.ledger_view(self.initial_render);
            });
        },

        print_pdf: function(e) {
            e.preventDefault();
            var self = this;
            self._rpc({
                model: 'dynamic.cash.flow',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'dynamic_financial_report.cash_flow',
                    'report_file': 'dynamic_financial_report.cash_flow',
                    'data': {
                        'report_data': data
                    },
                    'context': {
                        'active_model': 'dynamic.cash.flow',
                        'landscape': 1,
                        'js_report': true
                    },
                    'display_name': 'Cash Flow',
                };
                return self.do_action(action);
            });
        },

        print_xlsx: function() {
            var self = this;
            self._rpc({
                model: 'dynamic.cash.flow',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir_actions_xlsx_download',
                    'data': {
                         'model': 'dynamic.cash.flow',
                         'options': JSON.stringify(data[1]),
                         'output_format': 'xlsx',
                         'report_data': JSON.stringify(data[0]),
                         'report_name': 'Cash Flow',
                         'dfr_data': JSON.stringify(data),
                    },
                };
                return self.do_action(action);
            });
        },

        ledger_view: function(initial_render = true) {
            var self = this;
            var node = self.$('.container-cf-main');
            var last;
            while (last = node.lastChild) node.removeChild(last);
            rpc.query({
                model: 'dynamic.cash.flow',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(datas) {
                self.filter_data = datas[0]
                self.account_data = datas[1]
                console.log("account_data",self.account_data)
                _.each(self.account_data.fetched_data, function(account) {
                var currency_format = {
                        currency_id: datas[1].company_currency_id,
                        position: datas[1].company_currency_position,
                        symbol: datas[1].company_currency_symbol,

                        noSymbol: true,
                    };
                    if (currency_format.position == "before") {

                         if (account.total_credit == 0) {
                                account.total_credit = ' - '
                            } else {
                               account.total_credit = currency_format.symbol + '&nbsp;' + account.total_credit.toFixed(2) + '&nbsp;';

                            }
                            if (account.total_debit == 0) {
                                account.total_debit = ' - '

                            } else {
                                account.total_debit = currency_format.symbol + '&nbsp;' + account.total_debit.toFixed(2) + '&nbsp;';

                            }
                            if (account.total_balance == 0) {
                                account.total_balance = ' - '

                            } else {
                                account.total_balance = currency_format.symbol + '&nbsp;' + account.total_balance.toFixed(2) + '&nbsp;';

                            }



                        } else {if (account.total_credit == 0) {
                                account.total_credit = ' - '
                            } else {
                                account.total_credit = account.total_credit.toFixed(2) + '&nbsp;' + currency_format.symbol;
//
                            }
                            if (account.total_debit == 0) {
                                account.total_debit = ' - '

                            } else {
                                account.total_debit = account.total_debit.toFixed(2) + '&nbsp;' + currency_format.symbol;

                            }
                            if (account.total_balance == 0) {
                                account.total_balance  = ' - '
                            } else {
                                account.total_balance  = account.total_balance.toFixed(2) + '&nbsp;' + currency_format.symbol;

                            }
//
                        }
                });
                if (initial_render) {
                    self.$('.cf-filter').html(QWeb.render('FilterSectionCF', {
                        filter_data: datas[0],
                    }));

                    self.$el.find('.journal').select2({
                        placeholder: 'Select Journal...',
                    });
                    self.$el.find('.level').select2({
                        placeholder: 'Select Level...',
                    });

                     self.$el.find('.analytic-tag').select2({
                        placeholder: 'Select Analytic Tag...',
                    });
                    self.$el.find('.analytic').select2({
                        placeholder: 'Select Analytic...',
                    });

                    self.$el.find('#date_from').datepicker({
                        dateFormat: 'dd-mm-yy'
                    });
                    self.$el.find('#date_to').datepicker({
                        dateFormat: 'dd-mm-yy'
                    });
                    self.$el.find('.target-moves').select2({
                       placeholder: 'Posted or All Entries...',
                    });
                }

                self.$('.container-cf-main').html(QWeb.render('CashFlowData', {
                    account_data: datas[1].fetched_data,
                    level:datas[1].levels,
                }));

            });
        },




        get_move_lines: function(event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
            rpc.query({
                model: 'dynamic.cash.flow',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(datas) {

                    if(datas[1].levels== 'detailed'){
                        $(event.currentTarget).next('tr').find('td ul').after(
                            QWeb.render('SubSectionCF', {
                                count: 3,
                                offset: 0,
                                account_data: datas[1].journal_res,
                                level:datas[1].levels,
                                data_currency: datas[1],
                                line_id:parseInt(event.currentTarget.attributes[3].value),
                            }))
                    }else if(datas[1].levels== 'very'  || datas[1].levels== false){
                            $(event.currentTarget).next('tr').find('td ul').after(
                            QWeb.render('ChildSubSectionCF', {
                                count: 3,
                                offset: 0,
                                account_data: datas[1].account_res,
                                level:datas[1].levels,
                                data_currency: datas[1],
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
        view_move: function(event) {
            event.preventDefault();
            var self = this;
            var context = {};
            var redirect_to_document = function(res_model, res_id, view_id) {

                var action = {
                    type: 'ir.actions.act_window',
                    view_type: 'form',
                    view_mode: 'form',
                    res_model: res_model,
                    views: [
                        [view_id || false, 'form']
                    ],
                    res_id: res_id,
                    target: 'current',
                    context: context,
                };
                return self.do_action(action);
            };
            rpc.query({
                    model: 'account.move',
                    method: 'search_read',
                    domain: [
                        ['id', '=', $(event.currentTarget).data('move-id')]
                    ],
                    fields: ['id'],
                    limit: 1,
                })
                .then(function(record) {
                    if (record.length > 0) {
                        redirect_to_document('account.move', record[0].id);
                    } else {
                        redirect_to_document('account.move', $(event.currentTarget).data('move-id'));
                    }
                });
        },

    });

    core.action_registry.add('dynamic.cf', CashFlow);
        return CashFlow;


});