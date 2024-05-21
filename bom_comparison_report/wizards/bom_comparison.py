# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError


class BomComparison(models.TransientModel):
    """Model Used for the BOM comparison report Wizard"""
    _name = 'bom.comparison'
    _description = "Wizard for comparing boms "

    product_tmpl_id = fields.Many2one('product.template', string='Product', help='Choose the product')
    all_bom_ids = fields.Many2many('mrp.bom', compute='_compute_all_bom_ids',
                                   help='Used to get all the bom related to selected product')
    bom_ids = fields.Many2many('mrp.bom', domain="[('id','in',all_bom_ids)]", required=True, help='Choose the BOMs',
                               string='Bill of Materials')
    product_unit = fields.Integer(string='Number of Products to Produce', default=1,
                                  help='Set the number of products to produce')
    analysis = fields.Selection(selection=[('cost', 'Cost'), ('sale_price', 'Sales Price')], string='Analysis Method',
                                required=True, help='Choose the Analysis Method')

    @api.depends('product_tmpl_id')
    def _compute_all_bom_ids(self):
        """Compute function to Get all bom with the selected product"""
        for record in self:
            record.all_bom_ids = self.env['mrp.bom'].search(
                [('product_tmpl_id', '=', record.product_tmpl_id.id)]).ids

    def action_comparison_report(self):
        """Action for the Report Generation"""
        data = {
            'form_data': self.read()[0],
        }
        return self.env.ref('bom_comparison_report.bom_comparison_report_action').report_action(None, data=data)

    @api.constrains('bom_ids')
    def _check_bom_ids(self):
        """Constraints if No Boms to Compare"""
        if len(self.bom_ids) <= 1:
            raise ValidationError('The Comparison of BOMs Needs Minimum of two BOMs')

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """Clear the bom ids when the product changes"""
        self.update({
            'bom_ids': [(fields.Command.clear())]
        })
