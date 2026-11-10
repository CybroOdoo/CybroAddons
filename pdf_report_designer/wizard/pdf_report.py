# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PDFReportWizard(models.TransientModel):
    """Confirmation wizard shown by the contextual "Print Report" action"""
    _name = "pdf.report"
    _description = "PDF Report Wizard"
    _order = 'id DESC'

    def action_print_pdf_report(self):
        """Print the configured report for the records selected in the list
        or form view the contextual action was launched from."""
        self.ensure_one()
        report = self.env['report.pdf'].browse(
            self.env.context.get('pdf')).exists()
        if not report:
            raise UserError(_("The report configuration no longer exists."))
        active_model = self.env.context.get('active_model')
        if active_model != report.model_id.model:
            raise UserError(_(
                "This report is designed for the model %s.",
                report.model_id.model))
        records = self.env[active_model].browse(
            self.env.context.get('active_ids', [])).exists()
        return report.action_print_report(records=records)
