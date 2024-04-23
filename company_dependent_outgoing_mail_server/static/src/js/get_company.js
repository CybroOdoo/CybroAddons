/** @odoo-module **/
import { SwitchCompanyItem } from "@web/webclient/switch_company_menu/switch_company_menu";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
/**Returns the current company id to function get_company_id through rpc call**/
patch(SwitchCompanyItem.prototype,{
    setup(){
        this.orm = useService("orm");
        return super.setup()
    },
    logIntoCompany() {
        this.orm.call("ir.mail_server", "get_company_id", [this.props.company.id]);
        return super.logIntoCompany();
    }
});
