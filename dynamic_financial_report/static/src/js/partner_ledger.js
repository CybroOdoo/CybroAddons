odoo.define('dynamic_financial_report.partner_ledger', function(require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var _t = core._t;

    var PartnerLedger = AbstractAction.extend({
        template: 'PartnerLedger',
        events: {
            'click .pl-line': 'get_move_lines',
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
                model: 'dynamic.partner.ledger',
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
            var journal_ids = [];
            var journal_text = [];
            var span_res = document.getElementById("journal_res")
            var journal_list = $(".journal").select2('data')
            for (var i = 0; i < journal_list.length; i++) {
            if(journal_list[i].element[0].selected === true){ journal_ids.push(parseInt(journal_list[i].id))
            if(journal_text.includes(journal_list[i].text) === false){
            journal_text.push(journal_list[i].text)
            }
            span_res.value = journal_text
            span_res.innerHTML=span_res.value;
            }
            }
            if (journal_list.length == 0){
            span_res.value = ""
            span_res.innerHTML=""; }
            output.journal_ids = journal_ids


            var partner_ids = [];
            var partner_text = [];
            var span_res = document.getElementById("partner_res")
            var partner_list = $(".partner").select2('data')
            for (var i = 0; i < partner_list.length; i++) {
            if(partner_list[i].element[0].selected === true)
            {partner_ids.push(parseInt(partner_list[i].id))
            if(partner_text.includes(partner_list[i].text) === false)
            {partner_text.push(partner_list[i].text)
            }
            span_res.value = partner_text
            span_res.innerHTML=span_res.value;
            }
            }
            if (partner_list.length == 0){
            span_res.value = ""
            span_res.innerHTML=""; }
            output.partner_ids = partner_ids


            var account_ids = [];
            var account_text = [];
            var span_res = document.getElementById("account_res")
            var account_list = $(".account").select2('data')
            for (var i = 0; i < account_list.length; i++) {
            if(account_list[i].element[0].selected === true)
            {account_ids.push(parseInt(account_list[i].id))
            if(account_text.includes(account_list[i].text) === false)
            {account_text.push(account_list[i].text)
            }
            span_res.value = account_text
            span_res.innerHTML=span_res.value;
            }
            }
            if (account_list.length == 0){
            span_res.value = ""
            span_res.innerHTML=""; }
            output.account_ids = account_ids


            var partner_category_ids = [];
            var partner_category_text = [];
            var span_res = document.getElementById("category_res")
            var category_list = $(".category").select2('data')
            for (var i = 0; i < category_list.length; i++) {
            if(category_list[i].element[0].selected === true)
            {partner_category_ids.push(parseInt(category_list[i].id))
            if(partner_category_text.includes(category_list[i].text) === false)
            {partner_category_text.push(category_list[i].text)
            }
            span_res.value = partner_category_text
            span_res.innerHTML=span_res.value;
            }
            }
            if (category_list.length == 0){
            span_res.value = ""
            span_res.innerHTML=""; }
            output.partner_category_ids = partner_category_ids




            if ($(".reconcile").length){
            var reconciled_res = document.getElementById("reconciled_res")
            output.reconciled = $(".reconcile")[1].value
            reconciled_res.value = $(".reconcile")[1].value
            reconciled_res.innerHTML=reconciled_res.value;
            if ($(".reconcile").value==""){
            reconciled_res.innerHTML="unreconciled";
            output.reconciled = "unreconciled"
            }
            }


            if ($(".type").length){
            var type_res = document.getElementById("type_res")
            output.type = $(".type")[1].value
            type_res.value = $(".type")[1].value
            type_res.innerHTML=type_res.value;
            if ($(".type").value==""){
            type_res.innerHTML="receivable";
            output.type = "Receivable"
            }
            }

            if ($(".target-moves").length){
                var target_res = document.getElementById("target_res")
                output.target_moves = $(".target-moves")[1].value
                target_res.value = $(".target-moves")[1].value
                target_res.innerHTML=target_res.value;
            if ($(".target-moves").value==""){
                target_res.innerHTML="all_entries";
                output.target_moves = "all_entries"
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
                model: 'dynamic.partner.ledger',
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
                model: 'dynamic.partner.ledger',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'dynamic_financial_report.partner_ledger',
                    'report_file': 'dynamic_financial_report.partner_ledger',
                    'data': {
                        'report_data': data
                    },
                    'context': {
                        'active_model': 'dynamic.partner.ledger',
                        'landscape': 1,
                        'js_report': true
                    },
                    'display_name': 'Partner Ledger',
                };
                return self.do_action(action);
            });
        },
        print_xlsx: function() {
            var self = this;
            self._rpc({
                model: 'dynamic.partner.ledger',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir_actions_xlsx_download',
                    'data': {
                         'model': 'dynamic.partner.ledger',
                         'options': JSON.stringify(data[1]),
                         'output_format': 'xlsx',
                         'report_data': JSON.stringify(data[0]),
                         'report_name': 'Partner Ledger',
                         'dfr_data': JSON.stringify(data),
                    },

                };

                return self.do_action(action);
            });
        },

        ledger_view: function(initial_render = true) {
            var self = this;
            var node = self.$('.container-pl-main');
            var last;
            while (last = node.lastChild) node.removeChild(last);
            rpc.query({
                model: 'dynamic.partner.ledger',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(datas) {
                self.filter_data = datas[0]
                self.account_data = datas[1]

                _.each(self.account_data, function(account) {
                    var currency_format = {
                        currency_id: account.company_currency_id,
                        position: account.company_currency_position,
                        symbol: account.company_currency_symbol,
                        noSymbol: true,
                    };
                    if (currency_format.position == "before") {

                         if (account.debit == 0) {
                                account.debit = ' - '
                            } else {
                                account.debit = currency_format.symbol + '&nbsp;' + account.debit.toFixed(2) + '&nbsp;';

                            }
                            if (account.credit == 0) {
                                account.credit = ' - '

                            } else {
                                account.credit = currency_format.symbol + '&nbsp;' + account.credit.toFixed(2) + '&nbsp;';

                            }
                            if (account.balance == 0) {
                                account.balance = ' - '

                            } else {
                                account.balance = currency_format.symbol + '&nbsp;' + account.balance.toFixed(2) + '&nbsp;';

                            }
                    } else {

                        if (account.debit == 0) {
                                account.debit = ' - '
                            } else {
                                account.debit = account.debit.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account.credit == 0) {
                                account.credit = ' - '

                            } else {
                                account.credit = account.credit.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account.balance == 0) {
                                account.balance = ' - '
                            } else {
                                account.balance = account.balance.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                    }
                });
                if (initial_render) {
                    self.$('.pl-filter').html(QWeb.render('FilterSectionPl', {
                        filter_data: datas[0],
                    }));

                    self.$el.find('.journal').select2({
                        placeholder: 'Select Journal...',
                    });
                    self.$el.find('.account').select2({
                        placeholder: 'Select Account...',
                    });
                    self.$el.find('.partner').select2({
                        placeholder: 'Select Partner...',
                    });
                    self.$el.find('.reconcile').select2({
                        placeholder: 'Select Reconciled status...',
                    });
                    self.$el.find('.target-moves').select2({
                        placeholder: 'Posted or All Entries...',
                    });
                    self.$el.find('.type').select2({
                        placeholder: 'Select Account...',
                    });
                    self.$el.find('.category').select2({
                        placeholder: 'Select Category...',
                    });
                    self.$el.find('#date_from').datepicker({
                        dateFormat: 'dd-mm-yy'
                    });
                    self.$el.find('#date_to').datepicker({
                        dateFormat: 'dd-mm-yy'
                    });
                }

                self.$('.container-pl-main').html(QWeb.render('PartnerLedgerData', {
                    account_data: datas[1]
                }));

            });
        },
        pl_lines_by_page: function(offset, account_id) {
            var self = this;
            return rpc.query({
                model: 'dynamic.partner.ledger',
                method: 'pl_move_lines',
                args: [self.wizard, offset, account_id],
            })
        },
        get_move_lines: function(event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
                self.pl_lines_by_page(offset, account_id).then(function(datas) {
                    _.each(datas[2], function(data) {
                        var currency_format = {
                            currency_id: data.company_currency_id,
                            position: data.company_currency_position,
                            symbol: data.company_currency_symbol,
                            noSymbol: true,
                        };
                        if (currency_format.position == "before") {
                            if (data.debit == 0) {
                                data.debit = ' - '
                            } else {
                                data.debit = currency_format.symbol + '&nbsp;' + data.debit.toFixed(2) + '&nbsp;';

                            }
                            if (data.credit == 0) {
                                data.credit = ' - '

                            } else {
                                data.credit = currency_format.symbol + '&nbsp;' + data.credit.toFixed(2) + '&nbsp;';

                            }
                            if (data.balance == 0) {
                                data.balance = ' - '

                            } else {
                                data.balance = currency_format.symbol + '&nbsp;' + data.balance.toFixed(2) + '&nbsp;';

                            }
                        } else {
                            if (data.debit == 0) {
                                data.debit = ' - '
                            } else {
                                data.debit = data.debit.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.credit == 0) {
                                data.credit = ' - '

                            } else {
                                data.credit = data.credit.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.balance == 0) {
                                data.balance = ' - '
                            } else {
                                data.balance = data.balance.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }

                        }


                    });
                    $(event.currentTarget).next('tr').find('td .pl-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('SubSectionPl', {
                            count: datas[0],
                            offset: datas[1],
                            account_data: datas[2],
                        }))
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

    core.action_registry.add('dynamic.pl', PartnerLedger);

});