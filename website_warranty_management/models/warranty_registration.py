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
from odoo import api, fields, models


class WarrantyRegistration(models.Model):
    """ Warranty registration model to store warranty instances for products sold"""
    _name = 'warranty.registration'
    _description = 'Warranty Registration'
    _rec_name = 'sale_order_id'
    _inherit = ['mail.thread']

    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    serial_no = fields.Char(string='Serial Number')
    start_date = fields.Date(string='Start Date', default=fields.Date.context_today)
    expiry_date = fields.Date(string='Expiry Date', required=True)
    warranty_type = fields.Selection([
        ('full', 'Full Warranty'),
        ('reparable', 'Reparable')
    ], string="Warranty Type")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled')
    ], string='Status', default='active', compute='_compute_state', store=True, readonly=False)

    @api.depends('expiry_date')
    def _compute_state(self):
        """ Compute state based on expiry date"""
        today = fields.Date.context_today(self)
        for record in self:
            if record.state not in ['draft', 'cancel']:
                if record.expiry_date and record.expiry_date < today:
                    record.state = 'expired'
                elif record.expiry_date and record.expiry_date >= today:
                    record.state = 'active'

    @api.model
    def _scheduler_update_warranty_state(self):
        """ Scheduler to update warranty state daily"""
        registrations = self.search([('state', 'not in', ['draft', 'expired', 'cancel'])])
        registrations._compute_state()

    def action_send_confirmation_email(self):
        """ Send warranty confirmation email to customer"""
        template = self.env.ref('website_warranty_management.email_template_warranty_registration', raise_if_not_found=False)
        if template:
            for registration in self:
                registration.with_context(lang=registration.customer_id.lang).message_post_with_source(
                    template,
                    subtype_xmlid='mail.mt_comment',
                )
