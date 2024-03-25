# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Subina P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EventServiceLine(models.Model):
    """Model to manage the service lines of the event management"""
    _name = 'event.service.line'
    _description = "Event Management Line"

    service = fields.Selection(
        [('', '')], string="Services", required=True,
        help="List of the service that automatically adds to selection while"
             " install service modules")
    event_id = fields.Many2one('event.management', string="Event",
                               help="Name of the event")
    date_from = fields.Datetime(string="Start Date", required=True,
                                help="Start date of service")
    date_to = fields.Datetime(string="Date to", required=True,
                              help="End date of service")
    amount = fields.Float(string="Amount", readonly=True, help="Amount")
    state = fields.Selection([('done', 'Done'), ('pending', 'Pending')],
                             string="State", default="pending",
                             readonly=True, help="States of the each"
                                                 " service in service line")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id,
                                  help="Default currency of the company")
    invoiced = fields.Boolean(string="Invoiced", readonly=True,
                              help="Is this service invoiced")
    related_product_id = fields.Many2one('product.product',
                                         string="Related Product",
                                         help="Select the related service "
                                              "product")
    _sql_constraints = [('event_supplier_unique', 'unique(event_id, service)',
                         'Duplication Of Service In The Service Lines '
                         'Is not Allowed')]

    @api.constrains('date_from', 'date_to')
    def _check_date_to_date_from(self):
        """ Checking if end date less than start date
         if yes: Show a validation error"""
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('"Date to" cannot be set before '
                                        '"Date from".\n\n'
                                        'Check the "Date from" and "Date to" '
                                        'of the "%s" service' % rec.service))
