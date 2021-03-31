odoo.define('dynamic_financial_report.ageing_partner', function(require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var _t = core._t;

    var AgeingPartner = AbstractAction.extend({
        template: 'AgeingPartner',
        events: {
            'click .al-line': 'get_move_lines',
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
                model: 'dynamic.ageing.partner',
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
            output.type=false
            output.partner_type=false
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
            span_res.innerHTML=""; }
            output.partner_ids = partner_ids
            var partner_category_ids = [];
            var category_text = [];
            var span_res = document.getElementById("category_res")

            var category_list = $(".partner-tag").select2('data')
            for (var i = 0; i < category_list.length; i++) {

                if(category_list[i].element[0].selected === true)
                    {partner_category_ids.push(parseInt(category_list[i].id))
                    if(category_text.includes(category_list[i].text) === false)
                    {category_text.push(category_list[i].text)

                    }

                    span_res.value = category_text
                    span_res.innerHTML=span_res.value;
                    }
            }
            if (category_list.length == 0){
            span_res.value = ""
            span_res.innerHTML=""; }
            output.partner_category_ids = partner_category_ids

              if ($(".target-moves").length){
              var target_res = document.getElementById("target_res")
              output.target_moves = $(".target-moves")[1].value
              target_res.value = $(".target-moves")[1].value
                 target_res.innerHTML=target_res.value;
              if ($(".target-moves").value==""){
              target_res.innerHTML="draft";
              output.target_moves = "draft"
                }
              }

            if ($(".partner-type").length){
              var partner_type_res = document.getElementById("partner_type_res")
              output.partner_type = $(".partner-type")[1].value
              partner_type_res.value = $(".partner-type")[1].value
                 partner_type_res.innerHTML=partner_type_res.value;
              if ($(".partner-type").value==""){
              partner_type_res.innerHTML="customer";
              output.partner_type = "customer"
                }
              }

            if ($(".account").length){
              var type_res = document.getElementById("type_res")
              output.type = $(".account")[1].value
              type_res.value = $(".account")[1].value
                 type_res.innerHTML=type_res.value;
              if ($(".account").value==""){
              type_res.innerHTML="receivable";
              output.type = "receivable"
                }
              }

            if ($("#as_on_date").val()) {
                var dateObject = $("#as_on_date").datepicker("getDate");
                var dateString = $.datepicker.formatDate("yy-mm-dd", dateObject);
                output.as_on_date = dateString;
            }
            output.include_details = true;


            rpc.query({
                model: 'dynamic.ageing.partner',
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
                model: 'dynamic.ageing.partner',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(data) {


                var action = {
                    'type': 'ir.actions.report',
                    'report_type': 'qweb-pdf',
                    'report_name': 'dynamic_financial_report.ageing_partner',
                    'report_file': 'dynamic_financial_report.ageing_partner',
                    'data': {
                        'report_data': data
                    },
                    'context': {
                        'active_model': 'dynamic.ageing.partner',
                        'landscape': 1,
                        'js_report': true
                    },
                    'display_name': 'Ageing Partner Report',
                };
                return self.do_action(action);
            });
        },
        print_xlsx: function() {
            var self = this;
            self._rpc({
                model: 'dynamic.ageing.partner',
                method: 'get_data',
                args: [
                    [self.wizard]
                ],
            }).then(function(data) {


                var action = {
                    'type': 'ir_actions_xlsx_download',
                    'data': {
                         'model': 'dynamic.ageing.partner',
                         'options': JSON.stringify(data[1]),
                         'output_format': 'xlsx',
                         'report_data': JSON.stringify(data[0]),
                         'report_name': 'Partner Ageing',
                         'dfr_data': JSON.stringify(data),
                    },
                };

                return self.do_action(action);
            });
        },
        ledger_view: function(initial_render = true) {
            var self = this;
            var node = self.$('.container-al-main');
            var last;
            while (last = node.lastChild) node.removeChild(last);
            rpc.query({
                model: 'dynamic.ageing.partner',
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

                         if (account.total == 0) {
                                account.total = ' - '
                            } else {
                                account.total = currency_format.symbol + '&nbsp;' + account.total.toFixed(2) + '&nbsp;';

                            }
                            if (account.Not == 0) {
                                account.Not = ' - '

                            } else {
                                account.Not = currency_format.symbol + '&nbsp;' + account.Not.toFixed(2) + '&nbsp;';

                            }
                            if (account.value_20 == 0) {
                                account.value_20 = ' - '

                            } else {
                                account.value_20 = currency_format.symbol + '&nbsp;' + account.value_20.toFixed(2) + '&nbsp;';

                            }
                            if (account[2140] == 0) {
                                account[2140] = ' - '

                            } else {
                                account[2140] = currency_format.symbol + '&nbsp;' + account[2140].toFixed(2) + '&nbsp;';

                            }
                            if (account[4160] == 0) {
                                account[4160] = ' - '

                            } else {
                                account[4160] = currency_format.symbol + '&nbsp;' + account[4160].toFixed(2) + '&nbsp;';

                            }
                            if (account[6180] == 0) {
                                account[6180] = ' - '

                            } else {
                                account[6180] = currency_format.symbol + '&nbsp;' + account[6180].toFixed(2) + '&nbsp;';

                            }
                            if (account[81100] == 0) {
                                account[81100] = ' - '

                            } else {
                                account[81100] = currency_format.symbol + '&nbsp;' + account[81100].toFixed(2) + '&nbsp;';

                            }
                            if (account[100] == 0) {
                                account[100] = ' - '

                            } else {
                                account[100] = currency_format.symbol + '&nbsp;' + account[100].toFixed(2) + '&nbsp;';

                            }
                        } else {

                            if (account.total == 0) {
                                account.total = ' - '
                            } else {
                                account.total = account.total.toFixed(2) + '&nbsp;' + currency_id.symbol;
//
                            }
                            if (account.Not == 0) {
                                account.Not = ' - '

                            } else {
                                account.Not = account.Not.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account.value_20 == 0) {
                                account.value_20 = ' - '
                            } else {
                                account.value_20 = account.value_20.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account[2140] == 0) {
                                account[2140] = ' - '
                            } else {
                                account[2140] = account[2140].toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account[4160] == 0) {
                                account[4160] = ' - '
                            } else {
                                account[4160] = account[4160].toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account[6180] == 0) {
                                account[6180] = ' - '
                            } else {
                                account[6180] = account[6180].toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account[81100] == 0) {
                                account[81100] = ' - '
                            } else {
                                account[81100] = account[81100].toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (account[100] == 0) {
                                account[100] = ' - '
                            } else {
                                account[100] = account[100].toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                        }

                });
                if (initial_render) {
                    self.$('.al-filter').html(QWeb.render('FilterSection-al', {
                        filter_data: datas[0],
                    }));
                    self.$el.find('.account').select2({
                        placeholder: 'Select Account Type...',
                    });
                    self.$el.find('.partner-type').select2({
                        placeholder: 'Select Partner Type...',
                    });
                    self.$el.find('.partner-tag').select2({
                        placeholder: 'Select Partner Tag...',
                    });
                    self.$el.find('.partners').select2({
                        placeholder: 'Select Partners...',
                    });
                    self.$el.find('.target-moves').select2({
                       placeholder: 'Posted or All Entries...',
                    });
                    self.$el.find('#as_on_date').datepicker({
                        dateFormat: 'dd-mm-yy'
                    });

                }

                self.$('.container-al-main').html(QWeb.render('AgeingPartnerData', {
                    account_data: datas[1]
                }));

            });
        },
        al_lines_by_page: function(offset, account_id) {

            var self = this;
            return rpc.query({
                model: 'dynamic.ageing.partner',
                method: 'al_move_lines',
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
                self.al_lines_by_page(offset, account_id).then(function(datas) {

                    _.each(datas[2], function(data) {

                        var currency_format = {
                            currency_id: data.company_currency_id,
                            position: data.company_currency_position,
                            symbol: data.company_currency_symbol,
                            noSymbol: true,
                        };

                         if (currency_format.position == "before") {
                            if (data.range_0 == 0) {
                                data.range_0 = ' - '
                            } else {
                                data.range_0 = currency_format.symbol  + data.range_0.toFixed(2) ;

                            }
                            if (data.range_1 == 0) {
                                data.range_1 = ' - '

                            } else {
                                data.range_1 = currency_format.symbol  + data.range_1.toFixed(2) ;

                            }
                            if (data.range_2 == 0) {
                                data.range_2 = ' - '

                            } else {
                                data.range_2 = currency_format.symbol  + data.range_2.toFixed(2)  ;

                            }
                            if (data.range_3 == 0) {
                                data.range_3 = ' - '

                            } else {
                                data.range_3 = currency_format.symbol  + data.range_3.toFixed(2)  ;

                            }
                            if (data.range_4 == 0) {
                                data.range_4 = ' - '

                            } else {
                                data.range_4 = currency_format.symbol  + data.range_4.toFixed(2)  ;

                            }
                            if (data.range_5 == 0) {
                                data.range_5 = ' - '

                            } else {
                                data.range_5 = currency_format.symbol  + data.range_5.toFixed(2)  ;

                            }
                            if (data.range_6 == 0) {
                                data.range_6 = ' - '

                            } else {
                                data.range_6 = currency_format.symbol  + data.range_6.toFixed(2)  ;

                            }
                        } else {
                            if (data.range_0 == 0) {
                                data.range_0 = ' - '
                            } else {
                                data.range_0 = data.range_0.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.range_1 == 0) {
                                data.range_1 = ' - '

                            } else {
                                data.range_1 = data.range_1.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.range_2 == 0) {
                                data.range_2 = ' - '
                            } else {
                                data.range_2 = data.range_2.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.range_3 == 0) {
                                data.range_3 = ' - '
                            } else {
                                data.range_3 = data.range_3.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.range_4 == 0) {
                                data.range_4 = ' - '
                            } else {
                                data.range_4 = data.range_4.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.range_5 == 0) {
                                data.range_5 = ' - '
                            } else {
                                data.range_5 = data.range_5.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                            if (data.range_6 == 0) {
                                data.range_6 = ' - '
                            } else {
                                data.range_6 = data.range_6.toFixed(2) + '&nbsp;' + currency_id.symbol;

                            }
                        }


                    });
                    $(event.currentTarget).next('tr').find('td .al-table-div').remove();
                    $(event.currentTarget).next('tr').find('td ul').after(
                        QWeb.render('SubSection_al', {
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
    core.action_registry.add('dynamic.al', AgeingPartner);

});