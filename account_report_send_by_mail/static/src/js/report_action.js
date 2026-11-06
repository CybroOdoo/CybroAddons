/** @odoo-module **/
import { AccountReportButtonsBar } from "@account_reports/components/account_report/buttons_bar/buttons_bar";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { signal } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

patch(AccountReportButtonsBar.prototype, {
    //created send mail report and report actions are performed here.
    setup() {
        // super the setup
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService('action');
        this.popup = signal.ref();
        const options = typeof this.controller?.options === "function" ? this.controller.options() : this.controller?.options;
        this.report_id = options?.report_id || this.controller?.actionReportId;
    },
    close_button() {
        //          close the wizard
        const popup = typeof this.popup === "function" ? this.popup() : this.popup?.el;
        if (popup) {
            popup.style.display = "none";
        }
    },
    send_mail() {
        //          display the send mail wizard
        const popup = typeof this.popup === "function" ? this.popup() : this.popup?.el;
        if (popup) {
            popup.style.display = "block";
        }
    },
    send_current_report() {
        //      generate current pdf report and display on the mail wizard
        var self = this;
        var unfolded_list = [];
        var unfolded = false;
        var lines = (this.controller?.lines) || (typeof this.controller?.data === "function" ? this.controller.data()?.lines : this.controller?.data?.lines) || [];
        for (var line of lines) {
            if (line.unfolded == true) {
                unfolded_list.push(line.id);
            }
        }
        var options = typeof this.controller?.options === "function" ? this.controller.options() : this.controller?.options;
        var reportId = (options?.report_id) || this.controller?.actionReportId || this.report_id;
        this.orm.call('send.mail.report', 'send_current_report', [{}], {
            context: {
                report: reportId,
                unfolded_lines: unfolded_list,
                unfolded: unfolded,
                report_options: options,
            }
        }).then(function (pdf) {
            if (pdf) {
                self.actionService.doAction({
                    type: 'ir.actions.act_window',
                    name: _t('Send Mail'),
                    res_model: 'send.mail.report',
                    views: [[false, "form"]],
                    view_mode: 'form',
                    target: 'new',
                    context: {
                        'default_report': reportId,
                        'default_subject': 'Accounting Report',
                        'default_attachment_ids': [pdf],
                    },
                });
            }
        });
        this.close_button();
    },
    send_unfolded_report() {
        //       generate unfolded report pdf and display on the mail wizard
        var self = this;
        var options = typeof this.controller?.options === "function" ? this.controller.options() : this.controller?.options;
        var reportId = (options?.report_id) || this.controller?.actionReportId || this.report_id;
        this.orm.call('send.mail.report', 'send_unfolded_report', [{}], {
            context: {
                report: reportId,
                report_options: options,
            }
        }).then(function (pdf) {
            if (pdf) {
                self.actionService.doAction({
                    type: 'ir.actions.act_window',
                    name: _t('Send Mail'),
                    res_model: 'send.mail.report',
                    views: [[false, "form"]],
                    view_mode: 'form',
                    target: 'new',
                    context: {
                        'default_report': reportId,
                        'default_subject': 'Accounting Report',
                        'default_attachment_ids': [pdf],
                    },
                });
            }
        });
        this.close_button();
    },
})
