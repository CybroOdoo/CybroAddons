odoo.define('customize_settings.web_client',async function(require){
    'use strict';

    const{WebClient}=require("@web/webclient/webclient");
    const{patch}=require("@web/core/utils/patch");
    const{useService}=require("@web/core/utils/hooks");
    const{useOwnDebugContext}=require("@web/core/debug/debug_context");
    const{registry}=require("@web/core/registry");
    const{DebugMenu}=require("@web/core/debug/debug_menu");
    const{localization}=require("@web/core/l10n/localization");
    const{useTooltip}=require("@web/core/tooltip/tooltip_hook");
    const rpc=require('web.rpc');
    var session = require('web.session');

    patch(WebClient.prototype,"customize_settings.WebClient",{
        setup(){
            this.menuService=useService("menu");this._super()
            var domain = session.user_context.allowed_company_ids;
            var obj = this;
            rpc.query({
                fields: ['name','id',],
                domain: [['id', 'in', domain]],
                model: 'res.company',
                method: 'search_read',
            }).then(function (result) {
                obj.title.setParts({ zopenerp: result[0].name }); // Replacing the name 'Oodo' to selected company name near favicon
            });

        },
    });
});

