/** @odoo-module **/
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";
import { patch } from 'web.utils';
import { useService } from "@web/core/utils/hooks";
const rpc = require('web.rpc')
const { hooks } = owl;
const { useState } = hooks;
/**Returns the current company id to function get_company_id through rpc call**/
patch(SwitchCompanyMenu.prototype, "logIntoCompany", {
    setup() {
        this.companyService = useService("company");
        this.currentCompany = this.companyService.currentCompany;
        this.state = useState({ companiesToToggle: [] });
        rpc.query({
          model: "ir.mail_server",
          method: "get_company_id",
          args: [this.currentCompany]
        });
    },
});