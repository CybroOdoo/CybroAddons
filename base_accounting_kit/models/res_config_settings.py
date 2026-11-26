# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """Defines a model for configuration settings with additional fields for
     managing customer credit limit and Anglo-Saxon accounting settings."""
    _inherit = 'res.config.settings'

    customer_credit_limit = fields.Boolean(string="Customer Credit Limit")

    use_anglo_saxon_accounting = fields.Boolean(string="Use Anglo-Saxon accounting", readonly=False,
                                                related='company_id.anglo_saxon_accounting')
    # Fiscal year end of the company (core company fields), shown in the
    # "Fiscal Year" setting; Fiscal Years records take precedence.
    fiscalyear_last_day = fields.Integer(string="Fiscal Year End Day", readonly=False,
                                         related='company_id.fiscalyear_last_day')
    fiscalyear_last_month = fields.Selection(string="Fiscal Year End Month", readonly=False,
                                             related='company_id.fiscalyear_last_month')
    kit_auto_reconcile_import = fields.Boolean(
        related='company_id.kit_auto_reconcile_import', readonly=False)
    fx_reval_journal_id = fields.Many2one(
        related='company_id.fx_reval_journal_id', readonly=False)
    fx_reval_gain_account_id = fields.Many2one(
        related='company_id.fx_reval_gain_account_id', readonly=False)
    fx_reval_loss_account_id = fields.Many2one(
        related='company_id.fx_reval_loss_account_id', readonly=False)

    @api.model
    def get_values(self):
        """Retrieve the values for configuration settings including the
         customer credit limit from the database parameters. """
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        customer_credit_limit = params.get_bool('customer_credit_limit',
                                                 default=False)
        res.update(customer_credit_limit=customer_credit_limit)
        return res

    def set_values(self):
        """Set the customer credit limit value in the database parameters using superuser access."""
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_bool(
            "customer_credit_limit",
            self.customer_credit_limit)
