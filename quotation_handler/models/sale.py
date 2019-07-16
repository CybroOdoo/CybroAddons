# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nikhil krishnan(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
from datetime import timedelta, datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       index=True, default='New')
    parent_so_id = fields.Many2one('sale.order', 'Parent SO')
    revised_order_count = fields.Integer(string='# of Revised Orders', compute='_revised_count')
    validity_date = fields.Date(string='Expiration Date', readonly=True, states={'draft': [('readonly', False)],
                                                                                 'pre': [('readonly', False)]},
                                help="Automatically expiration date of your quotation (offer) will set as 14 days "
                                     "later, or it will set the date automatically based on the settings, We can set "
                                     "it manually too.")

    state = fields.Selection([
        ('pre', 'Revised Quotation'),
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('revised', 'Revised'),
        ('sale', 'Sale Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    revision_number = fields.Integer(string='Revision', copy=False, default=1)
    org_name = fields.Char(string='Origin', copy=False)

    @api.model
    def create(self, vals):
        date_start = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date_start')
        if not date_start:
            if 'validity_date' in vals:
                if vals.get('validity_date'):
                    pass
                else:
                    date_no = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date_no')
                    date_today = fields.Date.today()
                    date_object = datetime.strptime(date_today, '%Y-%m-%d')
                    if not date_no:
                        pass
                    else:
                        v_date = date_object + timedelta(days=date_no)
                        vals['validity_date'] = v_date

        return super(SaleOrder, self).create(vals)

    @api.multi
    def _revised_count(self):
        for sale in self:
            revised_count = sale.search([('parent_so_id', '=', sale.id)])
            sale.revised_order_count = len(revised_count)

    # ********************Overwrite the print button to give expiration date********************
    @api.multi
    def print_quotation(self):
        is_date = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date')
        date_start = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date_start')
        date_no = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date_no')
        if is_date:
            if date_start:
                if date_no:
                    for doc in self:
                        if doc.state in ['pre', 'draft']:
                            date_today = fields.Date.today()
                            date_object = datetime.strptime(date_today, '%Y-%m-%d')
                            v_date = date_object + timedelta(days=date_no)
                            doc.validity_date = v_date
        self.filtered(lambda s: s.state == 'pre').write({'state': 'sent'})
        return super(SaleOrder, self).print_quotation()

    @api.multi
    def make_revision(self):
        for rec in self:
            if not rec.org_name:
                namee = rec.name + '/R' + str(rec.revision_number)
                rec.org_name = rec.name
            else:
                namee = rec.org_name + '/R' + str(rec.revision_number)
            if not rec.org_name:
                names = rec.name
            else:
                names = rec.org_name
            vals = {
                'name': names + "-" + str(rec.revision_number),
                'state': 'revised',
                'parent_so_id': rec.id
            }
            new_so_copy = rec.copy(default=vals)
            rec.state = 'pre'
            rec.name = namee
            rec.revision_number += 1
            date_start = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date_start')
            if date_start:
                rec.validity_date = False


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'sale.order' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            order = self.env['sale.order'].browse([self._context['default_res_id']])
            # ********************Email Sent action Change the State in pre stage too********************
            if order.state in ('draft', 'pre'):
                order.state = 'sent'
                date_start = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date_start')
                if date_start:
                    # ********************Email Sent action Set the Exp Date From settings********************
                    date_no = self.env['ir.values'].get_default('sale.config.settings', 'so_expiration_date_no')
                    date_today = fields.Date.today()
                    date_object = datetime.strptime(date_today, '%Y-%m-%d')
                    if date_no:
                        v_date = date_object + timedelta(days=date_no)
                        order.validity_date = v_date

            self = self.with_context(mail_post_autofollow=True)
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)

