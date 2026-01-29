/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import session from "web.session";
var rpc = require('web.rpc');
var ExampleWidget = Widget.extend({
    template: 'LanguageSwitch',
    events: {
        'click .dropdown-menu': '_onLanguageSelect',
    },
//    Initializes the object by copying the current language and available languages
//    from the session object.
    init: function () {
        this.currentLang = [session.currentLang[0], session.currentLang[1]];
        this.availableLanguages = session.availableLanguages
    },
//    Handle the selection of language.
    _onLanguageSelect: function (ev) {
        var lang = ev.target.dataset.langKey
        rpc.query({
            model: 'res.users',
            method: 'write',
            args: [[session.uid], {
                "lang": lang
            }],
        }).then(() => {
            window.location.reload();
        });
    }
});
SystrayMenu.Items.push(ExampleWidget);
export default ExampleWidget;