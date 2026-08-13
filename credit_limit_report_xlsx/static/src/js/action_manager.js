/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("credit_limit_xlsx_handler", async (action, options, env) => {
	if (action.report_type === "credit_limit_xlsx") {
		env.services.ui.block();
		try {
			await download({
				url: "/credit_xlsx_reports",
				data: action.data,
			});
			return true;
		} catch (error) {
			console.error("XLSX Download Error:", error);
		} finally {
			env.services.ui.unblock();
		}
	}
});
