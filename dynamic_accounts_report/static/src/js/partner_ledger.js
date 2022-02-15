odoo.define('dynamic_accounts_report.partner_ledger', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var _t = core._t;

        var datepicker = require('web.datepicker');
    var time = require('web.time');

    window.click_num = 0;
    var PartnerLedger = AbstractAction.extend({
    template: 'PartnerTemp',
        events: {
            'click .parent-line': 'journal_line_click',
            'click .child_col1': 'journal_line_click',
            'click #apply_filter': 'apply_filter',
            'click #pdf': 'print_pdf',
            'click #xlsx': 'print_xlsx',
            'click .pl-line': 'show_drop_down',
            'click .view-account-move': 'view_acc_move',
            'mousedown div.input-group.date[data-target-input="nearest"]': '_onCalendarIconClick',

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
                model: 'account.partner.ledger',
                method: 'create',
                args: [{
                }]
            }).then(function(t_res) {
                self.wizard_id = t_res;
                self.load_data(self.initial_render);
            })
        },


        _onCalendarIconClick: function (ev) {
        var $calendarInputGroup = $(ev.currentTarget);

        var calendarOptions = {

        minDate: moment({ y: 1000 }),
            maxDate: moment().add(200, 'y'),
            calendarWeeks: true,
            defaultDate: moment().format(),
            sideBySide: true,
            buttons: {
                showClear: true,
                showClose: true,
                showToday: true,
            },

            icons : {
                date: 'fa fa-calendar',

            },
            locale : moment.locale(),
            format : time.getLangDateFormat(),
             widgetParent: 'body',
             allowInputToggle: true,
        };

        $calendarInputGroup.datetimepicker(calendarOptions);
    },

        load_data: function (initial_render = true) {
            var self = this;
                self.$(".categ").empty();
                try{
                    var self = this;
                    self._rpc({
                        model: 'account.partner.ledger',
                        method: 'view_report',
                        args: [[this.wizard_id]],
                    }).then(function(datas) {
                            _.each(datas['report_lines'], function(rep_lines) {
                            rep_lines.debit = self.format_currency(datas['currency'],rep_lines.debit);
                            rep_lines.credit = self.format_currency(datas['currency'],rep_lines.credit);
                            rep_lines.balance = self.format_currency(datas['currency'],rep_lines.balance);




                            });



                        if (initial_render) {
                            self.$('.filter_view_tb').html(QWeb.render('PLFilterView', {
                                filter_data: datas['filters'],
                            }));
                            self.$el.find('.journals').select2({
                                placeholder: ' Journals...',
                            });

                            self.$el.find('.account').select2({
                                placeholder: ' Accounts...',
                            });
                            self.$el.find('.partners').select2({
                            placeholder: 'Partners...',
                            });
                            self.$el.find('.reconciled').select2({
                            placeholder: 'Reconciled status...',
                            });
                            self.$el.find('.type').select2({
                            placeholder: 'Account Type...',
                            });
                            self.$el.find('.category').select2({
                            placeholder: 'Partner Tag...',
                            });
                            self.$el.find('.acc').select2({
                            placeholder: 'Select Acc...',
                            });
                        }
                        var child=[];

                        self.$('.table_view_tb').html(QWeb.render('PLTable', {
                            report_lines : datas['report_lines'],
                            filter : datas['filters'],
                            currency : datas['currency'],
                            credit_total : datas['credit_total'],
                            debit_total : datas['debit_total'],
                            debit_balance : datas['debit_balance']
                        }));
                    });

                }
                catch (el) {
                    window.location.href
                    }
            },



            format_currency: function(currency, amount) {
                if (typeof(amount) != 'number') {
                    amount = parseFloat(amount);
                }
                var formatted_value = (parseInt(amount)).toLocaleString(currency[2],{
                    minimumFractionDigits: 2
                })
                return formatted_value
            },

            print_pdf: function(e) {
            e.preventDefault();
            var self = this;
            self._rpc({
                model: 'account.partner.ledger',
                method: 'view_report',
                args: [
                    [self.wizard_id]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'dynamic_accounts_report.partner_ledger',
                    'report_file': 'dynamic_accounts_report.partner_ledger',
                    'data': {
                        'report_data': data
                    },
                    'context': {
                        'active_model': 'account.partner.ledger',
                        'landscape': 1,
                        'partner_ledger_pdf_report': true
                    },
                    'display_name': 'Partner Ledger',
                };
                return self.do_action(action);
            });
        },



        print_xlsx: function() {
            var self = this;
            self._rpc({
                model: 'account.partner.ledger',
                method: 'view_report',
                args: [
                    [self.wizard_id]
                ],
            }).then(function(data) {
                var action = {
                    'type': 'ir_actions_dynamic_xlsx_download',
                    'data': {
                         'model': 'account.partner.ledger',
                         'options': JSON.stringify(data['filters']),
                         'output_format': 'xlsx',
                         'report_data': JSON.stringify(data['report_lines']),
                         'report_name': 'Partner Ledger',
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

        show_drop_down: function(event) {
            event.preventDefault();
            var self = this;
            var account_id = $(event.currentTarget).data('account-id');
            var offset = 0;
            var td = $(event.currentTarget).next('tr').find('td');
            if (td.length == 1) {
                   self._rpc({
                        model: 'account.partner.ledger',
                        method: 'view_report',
                        args: [
                            [self.wizard_id]
                        ],
                    }).then(function(data) {
                     _.each(data['report_lines'], function(rep_lines) {
                            _.each(rep_lines['move_lines'], function(move_line) {

                             move_line.debit = self.format_currency(data['currency'],move_line.debit);
                            move_line.credit = self.format_currency(data['currency'],move_line.credit);
                            move_line.balance = self.format_currency(data['currency'],move_line.balance);


                             });
                             });
                    for (var i = 0; i < data['report_lines'].length; i++) {

                        if (account_id == data['report_lines'][i]['id'] ){
                            $(event.currentTarget).next('tr').find('td .pl-table-div').remove();
                            $(event.currentTarget).next('tr').find('td ul').after(
                                QWeb.render('SubSectionPL', {
                                    account_data: data['report_lines'][i]['move_lines'],
                                }))
                            $(event.currentTarget).next('tr').find('td ul li:first a').css({
                                'background-color': '#00ede8',
                                'font-weight': 'bold',
                                });
                             }
                        }
                    });
            }
        },

        view_acc_move: function(event) {
            event.preventDefault();
            var self = this;
            var context = {};
            var show_acc_move = function(res_model, res_id, view_id) {
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
                        show_acc_move('account.move', record[0].id);
                    } else {
                        show_acc_move('account.move', $(event.currentTarget).data('move-id'));
                    }
                });
        },

        apply_filter: function(event) {
            event.preventDefault();
            var self = this;
            self.initial_render = false;
            var filter_data_selected = {};

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
            filter_data_selected.account_ids = account_ids


            var journal_ids = [];
            var journal_text = [];
            var journal_res = document.getElementById("journal_res")
            var journal_list = $(".journals").select2('data')
            for (var i = 0; i < journal_list.length; i++) {
                if(journal_list[i].element[0].selected === true){
                    journal_ids.push(parseInt(journal_list[i].id))
                    if(journal_text.includes(journal_list[i].text) === false){
                        journal_text.push(journal_list[i].text)
                    }
                    journal_res.value = journal_text
                    journal_res.innerHTML=journal_res.value;
                }
            }
            if (journal_list.length == 0){
               journal_res.value = ""
                    journal_res.innerHTML="";
            }
            filter_data_selected.journal_ids = journal_ids

            var partner_ids = [];
            var partner_text = [];
            var span_res = document.getElementById("partner_res")
            var partner_list = $(".partners").select2('data')
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
            span_res.innerHTML="";
            }
            filter_data_selected.partner_ids = partner_ids

            var account_type_ids = [];
            var account_type_ids_text = [];
            var span_res = document.getElementById("type_res")
            var type_list = $(".type").select2('data')
            for (var i = 0; i < type_list.length; i++) {
            if(type_list[i].element[0].selected === true)
            {account_type_ids.push(parseInt(type_list[i].id))
            if(account_type_ids_text.includes(type_list[i].text) === false)
            {account_type_ids_text.push(type_list[i].text)
            }
            span_res.value = account_type_ids_text
            span_res.innerHTML=span_res.value;
            }
            }
            if (type_list.length == 0){
            span_res.value = ""
            span_res.innerHTML="";
            }
            filter_data_selected.account_type_ids = account_type_ids

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
            span_res.innerHTML="";
            }
            filter_data_selected.partner_category_ids = partner_category_ids

//            if ($("#date_from").val()) {
//                var dateString = $("#date_from").val();
//                filter_data_selected.date_from = dateString;
//            }
//            if ($("#date_to").val()) {
//                var dateString = $("#date_to").val();
//                filter_data_selected.date_to = dateString;
//            }

            if (this.$el.find('.datetimepicker-input[name="date_from"]').val()) {
                filter_data_selected.date_from = moment(this.$el.find('.datetimepicker-input[name="date_from"]').val(), time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
            }

            if (this.$el.find('.datetimepicker-input[name="date_to"]').val()) {
                filter_data_selected.date_to = moment(this.$el.find('.datetimepicker-input[name="date_to"]').val(), time.getLangDateFormat()).locale('en').format('YYYY-MM-DD');
            }

            if ($(".reconciled").length){
            var reconciled_res = document.getElementById("reconciled_res")
            filter_data_selected.reconciled = $(".reconciled")[0].value
            reconciled_res.value = $(".reconciled")[0].value
            reconciled_res.innerHTML=reconciled_res.value;
            if ($(".reconciled").value==""){
                reconciled_res.innerHTML="unreconciled";
                filter_data_selected.reconciled = "unreconciled"
                }
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
                model: 'account.partner.ledger',
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
    core.action_registry.add("p_l", PartnerLedger);
    return PartnerLedger;
});
