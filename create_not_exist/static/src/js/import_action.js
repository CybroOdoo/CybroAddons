odoo.define('create_not_exist.import', function (require) {
"use strict";
var config = require('web.config');
var core = require('web.core');
var session = require('web.session');
var time = require('web.time');
var AbstractWebClient = require('web.AbstractWebClient');
var Loading = require('web.Loading');
var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;
var StateMachine = window.StateMachine;
console.log('testtteeee');
var ImportAction = require('base_import.import').DataImport;
console.log("option2");
ImportAction.include({
onpreview_success: function (event, from, to, result) {
        var self = this;
        this.$buttons.filter('.oe_import_file')
            .text(_t('Load New File'))
            .removeClass('btn-primary').addClass('btn-secondary')
            .blur();
        this.$buttons.filter('.o_import_import, .o_import_validate, .o_import_file_reload').removeClass('d-none');
        this.$form.find('.oe_import_box, .oe_import_with_file').removeClass('d-none');
        this.$form.find('.o_view_nocontent').addClass('d-none');
        this.$form.addClass('oe_import_preview');
        this.$('input.oe_import_advanced_mode').prop('checked', result.advanced_mode);
        this.$('.oe_import_grid').html(QWeb.render('ImportView.preview', result));

        this.$('.o_import_batch_alert').toggleClass('d-none', !result.batch);

        var messages = [];
        if (result.headers.length === 1) {
            messages.push({type: 'warning', message: _t("A single column was found in the file, this often means the file separator is incorrect")});
        }

        if (!_.isEmpty(messages)) {
            this.$('.oe_import_options').show();
            this.onresults(null, null, null, {'messages': messages});
        }

        // merge option values back in case they were updated/guessed
        _.each(['encoding', 'separator', 'float_thousand_separator', 'float_decimal_separator'], function (id) {
            self.$('.oe_import_' + id).select2('val', result.options[id])
        });
        this.$('.oe_import_date_format').select2('val', time.strftime_to_moment_format(result.options.date_format));
        this.$('.oe_import_datetime_format').val(time.strftime_to_moment_format(result.options.datetime_format));
        // hide all "true debug" options when not in debug mode
        this.$('.oe_import_debug_option').toggleClass('d-none', !result.debug);

        var $fields = this.$('.oe_import_fields input');
        this.render_fields_matches(result, $fields);
        var data = this.generate_fields_completion(result);
        var item_finder = function (id, items) {
            items = items || data;
            for (var i=0; i < items.length; ++i) {
                var item = items[i];
                if (item.id === id) {
                    return item;
                }
                var val;
                if (item.children && (val = item_finder(id, item.children))) {
                    return val;
                }
            }
            return '';
        };
        $fields.each(function (k,v) {
            var filtered_data = self.generate_fields_completion(result, k);

            var $thing = $();
            var bind = function (d) {};
                bind = function (data) {
                    $thing = $(QWeb.render('ImportView.create_record_option')).insertAfter(v).hide();
                    switch (data.type) {
                    case 'many2one': case 'many2many': case 'one2many':
                        $thing.find('input').attr('field', data.id);
                        $thing.show();
                        break;
                    default:
                        $thing.find('input').attr('field', '').prop('checked', false);
                        $thing.hide();
                    }
                }

            $(v).select2({
                allowClear: true,
                minimumInputLength: 0,
                data: filtered_data,
                initSelection: function (element, callback) {
                    var default_value = element.val();
                    if (!default_value) {
                        callback('');
                        return;
                    }

                    var data = item_finder(default_value);
                    bind(data);
                    callback(data);
                },
                placeholder: _t('Don\'t import'),
                width: 'resolve',
                dropdownCssClass: 'oe_import_selector'
            }).on('change', function (e) {
                bind(item_finder(e.currentTarget.value));
            });
        });
    },
});
})
