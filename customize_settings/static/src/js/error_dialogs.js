odoo.define('customize_settings.error_dialogs', function(require){
    'use strict';

    const { odooExceptionTitleMap, ErrorDialog, ClientErrorDialog, NetworkErrorDialog,
    RPCErrorDialog, WarningDialog, SessionExpiredDialog } = require("@web/core/errors/error_dialogs");
    const { patch } = require("@web/core/utils/patch");
    const { _lt } = require("@web/core/l10n/translation");

    ErrorDialog.title=_lt("System Error");

    ClientErrorDialog.title = _lt('System Client Error');

    SessionExpiredDialog.title = _lt('System Session Expired');

    NetworkErrorDialog.title = _lt('System Network Expired');

    patch(RPCErrorDialog.prototype, 'customize_settings.RPCErrorDialog',{
        inferTitle() {
            if (this.props.exceptionName && odooExceptionTitleMap.has(this.props.exceptionName)) {
                this.title = odooExceptionTitleMap.get(this.props.exceptionName).toString();
                return;
            }
            if (!this.props.type) {
                return;
            }
            switch (this.props.type) {
                case "server":
                    this.title = this.env._t("System Server Error");
                    break;
                case "script":
                    this.title = this.env._t("System Client Error");
                    break;
                case "network":
                    this.title = this.env._t("System Network Error");
                    break;
            }
        }
    });

    patch(WarningDialog.prototype, 'customize_settings.WarningDialog',{
        setup() {
            super.setup();
            this.title = this.env._t("System Warning");
        }
    });

});
