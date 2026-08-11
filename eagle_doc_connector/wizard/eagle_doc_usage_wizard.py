# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from datetime import date
from odoo import api, fields, models, _
from odoo.addons.eagle_doc_connector.models.eagle_api import EagleDocAPI

EAGLE_DOC_USAGE_FEATURE_LABELS = {
    'OCR': 'OCR (Pages Processed)',
    'BOOKKEEPING': 'Bookkeeping Entries Created',
    'WRITE_DOCUMENTS': 'Invoices Created',
    'MULTIPLE_CLIENTS_OF_TAX_FIRM': 'Managed Clients (Tax Firm)',
}

MONTH_SELECTION = [
    ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
    ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
    ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'),
]

def _year_selection(self):
    """Get selection list of the last 5 years."""
    current_year = date.today().year
    return [(str(year), str(year)) for year in range(current_year - 4, current_year + 1)]

class EagleDocUsageWizardLine(models.TransientModel):
    """One feature/quantity row of usage displayed by the usage wizard."""

    _name = 'eagle.doc.usage.wizard.line'
    _description = 'Eagle Doc Usage Line'

    wizard_id = fields.Many2one('eagle.doc.usage.wizard', required=True, ondelete='cascade')
    feature_label = fields.Char(string="Feature")
    quantity = fields.Integer(string="Quantity")

class EagleDocUsageWizard(models.TransientModel):
    """Popup for browsing Eagle Doc's metered usage by billing period."""

    _name = 'eagle.doc.usage.wizard'
    _description = 'Eagle Doc Usage'

    period_month = fields.Selection(MONTH_SELECTION, string="Month", required=True)
    period_year = fields.Selection(_year_selection, string="Year", required=True)
    period = fields.Char(string="Billing Period", readonly=True)
    line_ids = fields.One2many('eagle.doc.usage.wizard.line', 'wizard_id', string="Usage", readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Default the period picker to the current month/year."""
        res = super().default_get(fields_list)
        today = date.today()
        res.setdefault('period_month', f"{today.month:02d}")
        res.setdefault('period_year', str(today.year))
        return res

    def action_fetch(self):
        """Fetch and refresh usage lines for the selected period."""
        self.ensure_one()
        period = f"{self.period_year}-{self.period_month}"
        api_client = EagleDocAPI(self.env)
        result = api_client.get_usage(period=period)
        totals = result.get('totals', {})
        resolved_period = result.get('period', period)
        self.line_ids.unlink()
        lines = [
            (0, 0, {
                'feature_label': EAGLE_DOC_USAGE_FEATURE_LABELS.get(key, key),
                'quantity': qty,
            })
            for key, qty in totals.items()
        ]
        self.write({'period': resolved_period, 'line_ids': lines})
        return {
            'type': 'ir.actions.act_window',
            'name': _("Eagle Doc Usage"),
            'res_model': 'eagle.doc.usage.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    @api.model
    def _open_usage_wizard(self):
        """Create and open a new usage wizard."""
        wizard = self.create({})
        return wizard.action_fetch()
