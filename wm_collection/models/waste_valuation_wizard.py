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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WasteValuationWizard(models.TransientModel):
    """Wizard to generate market valuation and financial balance reports for waste inventory."""
    _name = 'waste.valuation.wizard'
    _description = 'Waste Inventory Valuation Report Wizard'

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date', default=fields.Date.today)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    category_id = fields.Many2one('wm.waste.category', string='Category')
    product_id = fields.Many2one('product.product', string='Material/Product', domain="[('is_waste_material', '=', True)]")
    status = fields.Selection([
        ('received', 'Received'),
        ('sorting', 'Sorting'),
        ('sorted', 'Sorted'),
        ('recycled', 'Recycled'),
        ('sold', 'Sold'),
    ], string='Status')

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """ Validate that To Date is not earlier than From Date. """
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError(_("To Date cannot be earlier than From Date."))

    def action_print_report(self):
        """
        Generate the waste batch valuation PDF report using current market
        prices, recovered quantities, and category breakdowns as configured in
        the wizard.
        """
        domain = []
        if self.date_from:
            domain.append(('received_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('received_date', '<=', self.date_to))
        if self.warehouse_id:
            domain.append(('warehouse_id', '=', self.warehouse_id.id))
        if self.category_id:
            domain.append(('line_ids.category_id', '=', self.category_id.id))
        if self.product_id:
            domain.append(('line_ids.product_id', '=', self.product_id.id))
        if self.status:
            domain.append(('status', '=', self.status))

        batches = self.env['waste.batch'].search(
            domain, order='received_date desc, name'
        )
        return self.env.ref(
            'wm_collection.action_waste_valuation_report'
        ).report_action(batches)
