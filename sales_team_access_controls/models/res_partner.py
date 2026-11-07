# -*- coding: utf-8 -*-
#############################################################################
#
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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Inverse relations used by the contact restriction in
    # security/sales_team_access_controls_security.xml, so that a contact
    # stays readable when it is used on a lead or as an invoice/delivery
    # address of an order the user can read.
    team_access_lead_ids = fields.One2many(
        'crm.lead', 'partner_id', string='All Leads',
        context={'active_test': False})
    team_access_invoice_order_ids = fields.One2many(
        'sale.order', 'partner_invoice_id', string='Invoiced Orders')
    team_access_shipping_order_ids = fields.One2many(
        'sale.order', 'partner_shipping_id', string='Delivered Orders')
