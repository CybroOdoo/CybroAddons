# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class WmMonthlyBillingWizard(models.TransientModel):
    """Wizard to launch ad-hoc or backfill monthly billing runs."""
    _name = 'wm.monthly.billing.wizard'
    _description = 'Monthly Billing Wizard'

    period_start = fields.Date(
        string='Period Start',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    period_end = fields.Date(
        string='Period End',
        required=True,
        default=lambda self: fields.Date.today(),
    )
    partner_ids = fields.Many2many(
        'res.partner',
        string='Target Partners',
        help="Optional partner filter. Leave empty to process all partners.",
    )

    def action_run_monthly_billing(self):
        """
        Create a monthly billing run and trigger consolidation.
        """
        self.ensure_one()
        if self.period_end < self.period_start:
            raise UserError(_("Period End date cannot be earlier than Period Start date."))

        run = self.env['wm.monthly.billing.run'].create({
            'period_start': self.period_start,
            'period_end': self.period_end,
            'partner_ids': [(6, 0, self.partner_ids.ids)] if self.partner_ids else False,
        })
        run.action_run_billing()

        return {
            'name': _('Monthly Billing Run'),
            'type': 'ir.actions.act_window',
            'res_model': 'wm.monthly.billing.run',
            'res_id': run.id,
            'view_mode': 'form',
            'target': 'current',
        }
