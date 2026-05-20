# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class OilJVPartner(models.Model):
    """
    Working interest per partner within a JOA. Each line represents one
    partner's share, their receivable/payable accounts for JV transactions,
    and whether they are the operator.
    """
    _name = 'oil.jv.partner'
    _description = 'JV Partner Working Interest'
    _order = 'working_interest desc'

    agreement_id = fields.Many2one(
        'oil.jv.agreement',
        string='JOA',
        required=True,
        ondelete='cascade',
        help="The Joint Operating Agreement this partner belongs to.")
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        help="The JV partner company.")
    working_interest = fields.Float(
        string='Working Interest (%)',
        digits=(6, 4),
        required=True,
        help="Partner's working interest percentage in this JOA.")
    net_revenue_interest = fields.Float(
        string='Net Revenue Interest (%)',
        digits=(6, 4),
        help="Partner's net revenue interest after burdens (royalties, etc.).")
    is_operator = fields.Boolean(
        string='Is Operator',
        default=False,
        help="Whether this partner is the operator of the JV.")
    jv_receivable_account_id = fields.Many2one(
        'account.account',
        string='JV Receivable Account',
        help="Account used for billing this partner their share of costs.")
    jv_payable_account_id = fields.Many2one(
        'account.account',
        string='JV Payable Account',
        help="Account used when this partner bills the JV.")
    jv_revenue_account_id = fields.Many2one(
        'account.account',
        string='JV Revenue Account',
        help="Account for this partner's share of JV revenue.")
    currency_id = fields.Many2one(
        related='agreement_id.currency_id',
        help="Currency from the parent JOA.")
    company_id = fields.Many2one(
        related='agreement_id.company_id',
        store=True,
        help="Company from the parent JOA.")
    notes = fields.Text(
        string='Notes',
        help="Additional notes about this partner's participation.")

    @api.constrains('working_interest')
    def _check_working_interest(self):
        """Validates working interest is between 0 and 100."""
        for record in self:
            if record.working_interest <= 0 or record.working_interest > 100:
                raise ValidationError(
                    _("Working interest must be between 0 and 100%% for "
                      "partner '%s'.", record.partner_id.name))

    @api.constrains('net_revenue_interest')
    def _check_nri(self):
        """Validates NRI is between 0 and 100 if set."""
        for record in self:
            if record.net_revenue_interest:
                if record.net_revenue_interest < 0 or record.net_revenue_interest > 100:
                    raise ValidationError(
                        _("Net revenue interest must be between 0 and 100%% "
                          "for partner '%s'.", record.partner_id.name))

    @api.constrains('partner_id', 'agreement_id')
    def _check_unique_partner(self):
        """Ensures each partner appears only once per agreement."""
        for record in self:
            duplicates = self.search([
                ('agreement_id', '=', record.agreement_id.id),
                ('partner_id', '=', record.partner_id.id),
                ('id', '!=', record.id),
            ])
            if duplicates:
                raise ValidationError(
                    _("Partner '%s' already exists in this JOA.",
                      record.partner_id.name))
