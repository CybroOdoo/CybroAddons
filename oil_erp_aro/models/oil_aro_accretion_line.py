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

from odoo import fields, models

class OilAroAccretionLine(models.Model):
    """
    One row per accretion posting (monthly / quarterly / annual).

    Provides the period-by-period audit trail of how the ARO liability
    has accreted from its initial PV up to its current balance.
    """
    _name = 'oil.aro.accretion.line'
    _description = 'ARO Accretion Schedule Line'
    _order = 'date desc, id desc'

    display_name = fields.Char(compute='_compute_display_name', help="A unique name or reference identifier used to track this record in the system.")

    def _compute_display_name(self):
        """Calculates and updates the 'name' value automatically based on related operational inputs."""
        for rec in self:
            rec.display_name = f"{rec.obligation_id.name or ''} - {rec.date or ''}"

    obligation_id = fields.Many2one('oil.aro.obligation', string='ARO Obligation', required=True,
                                    ondelete='cascade', help="Link this transaction or record to the corresponding 'aro obligation' reference.")
    date = fields.Date(string='Posting Date', required=True, help="The date when this transaction, measurement, or event was officially recorded.")
    opening_balance = fields.Monetary(string='Opening Balance', currency_field='currency_id', help="Specify the numerical measurement, volume, or financial amount for 'opening balance'.")
    accretion_amount = fields.Monetary( string='Accretion', currency_field='currency_id', help="The unit rate or total financial cost applied to this transaction.")
    closing_balance = fields.Monetary(string='Closing Balance', currency_field='currency_id', help="Specify the numerical measurement, volume, or financial amount for 'closing balance'.")
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, help="Link this transaction or record to the corresponding 'journal entry' reference.")
    currency_id = fields.Many2one('res.currency', related='obligation_id.currency_id',
                                  store=True, readonly=True, help="Link this transaction or record to the corresponding 'currency id' reference.")
    company_id = fields.Many2one('res.company', related='obligation_id.company_id',
                                 store=True, readonly=True, help="The company managing this operational record or transaction.")
    notes = fields.Char(string='Notes', help="Additional comments, details, or operational remarks about this record.")
