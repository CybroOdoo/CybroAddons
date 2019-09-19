# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhilesh N S (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    care_of_partner_id = fields.Many2one('res.partner', string='Care Of (C/O)', required=False,
                                         help="To address a contact in care of someone else")
    care_of_percentage = fields.Float(string='C/O Commission Percentage')
    total_care_of_commission = fields.Monetary('C/O Total Commission',
                                               compute='_compute_total_care_of_commission',
                                               default=0.0)

    @api.multi
    def _compute_total_care_of_commission(self):
        """Compute total C/O commission amount received by a partner"""
        for rec in self:
            invoices = self.env['account.invoice'].search([('care_of_partner_id', '=', rec.id),
                                                           ('state', 'not in', ('draft', 'cancel'))])
            if invoices:
                rec.total_care_of_commission = sum(inv.care_of_commission for inv in invoices)

    @api.multi
    def action_view_care_of_invoices(self):
        """Show all invoice records having current contact as C/O Partner"""
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        invoices = self.env['account.invoice'].search([('care_of_partner_id', '=', self.id),
                                                       ('state', 'not in', ('draft', 'cancel'))])
        action['domain'] = [
            ('id', 'in', invoices.ids),
        ]
        return action

    @api.onchange('care_of_partner_id')
    def onchange_care_of_partner_id(self):
        self.care_of_percentage = self.env['ir.config_parameter'].sudo().\
            get_param('care_of_partner.commission') \
            if self.care_of_partner_id else None
