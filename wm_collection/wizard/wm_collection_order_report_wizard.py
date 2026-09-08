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
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WmCollectionOrderReportWizard(models.TransientModel):
    """Wizard for printing Collection Order Summary Report."""
    _name = 'wm.collection.order.report.wizard'
    _description = 'Collection Order Report Wizard'

    date_from = fields.Date(
        string='From Date', required=True,
        default=lambda self: fields.Date.context_today(self) - timedelta(days=30))
    date_to = fields.Date(
        string='To Date', required=True,
        default=lambda self: fields.Date.context_today(self))
    order_id = fields.Many2one('wm.collection.order', string='Order Number')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('dispatched', 'Dispatched'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('signed', 'Signed'),
        ('invoiced', 'Invoiced'),
        ('missed', 'Missed'),
        ('cancel', 'Cancelled'),
    ], string='Status')
    product_id = fields.Many2one('product.product', string='Waste Material')
    route_id = fields.Many2one('wm.route', string='Route')

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """
        Validate that To Date is not earlier than From Date.
        """
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError(_("To Date cannot be earlier than From Date."))

    def action_print_pdf(self):
        """
        Generate the collection order route sheet PDF for the selected date
        range and driver, combining all order details, waste weights, and
        collection point signatures.
        """
        self.ensure_one()
        return self.env.ref(
            'wm_collection.action_report_wm_collection_order_summary'
        ).report_action(self)
