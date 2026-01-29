/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
var ajax = require('web.ajax');
var LanguageWidget = Widget.extend({
    template: 'LanguageSystray',
    events: {
        'change #language_selector': '_onChangeLang',
    },
    /**
     Call the render_language function before loading the page
     */
    willStart: function() {
        var self = this;
        return this._super().then(function() {
            self.render_language();
        });
    },
    /**
     Adding activated language in the selection field in systray
     */
    render_language: function() {
        var self = this;
        ajax.rpc('/easy_language_selector/options').then(function(data) {
            var languages = data
            for(var i = 0; i < data.length; i++) {
                self.$el.find('#language_selector').append("<option class='language_options' value=" + data[i].code + ">" + data[i].name + "</option>");
            };
            self.$el.find('#language_selector').append("<option class='language_options' value='add_extra_lang'> Add Language </option>")
        });
    },
    /**
     Changing the language by changing the options
     */
    _onChangeLang: function() {
        console.log(this)
        var lang_code = this.$el.find("#language_selector").val();
        if (lang_code == "add_extra_lang") {
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Languages',
                res_model: 'res.lang',
                view_mode: 'list',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'self'
            });
        } else {
            ajax.rpc('/easy_language_selector/change', {
                'data': lang_code
            }).then(function() {
                window.location.reload();
            })
        }
    },
});
SystrayMenu.Items.push(LanguageWidget);
export default LanguageWidget;