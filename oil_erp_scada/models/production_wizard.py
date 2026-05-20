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
from odoo.tools.translate import _

class ProductionWizard(models.TransientModel):
    _inherit = 'production.wizard'

    storage_location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        domain=[('usage', '=', 'internal')],
        help="Select the storage location for the produced products.",
    )
    lease_id = fields.Many2one(
        'oil.lease.agreement',
        string='Lease Agreement',
        help="Select the lease/royalty agreement for this production."
    )

    def action_confirm(self):
        # Call super to create the stock picking
        res = super(ProductionWizard, self).action_confirm()
        
        # Find the picking that was just created.
        picking = self.env['stock.picking'].search([
            ('origin', '=', _('Production - %s', self.task_id.display_name)),
            ('scheduled_date', '=', self.production_date),
            ('location_dest_id', '=', self.storage_location_id.id),
        ], order='id desc', limit=1)

        if picking:
            # Aggregate volumes from wizard lines
            gas_vol = 0.0
            water_vol = 0.0
            
            for line in self.line_ids:
                product_name = line.product_id.name.lower()
                if 'gas' in product_name:
                    gas_vol += line.produced_qty
                elif 'water' in product_name:
                    water_vol += line.produced_qty

            # Create oil.daily.production record
            daily_production = self.env['oil.daily.production'].create({
                'well_id': self.task_id.id,
                'report_date': self.production_date,
                'storage_location_id': self.storage_location_id.id,
                'lease_id': self.lease_id.id,
                'picking_id': picking.id,
                'source': 'manual',
            })
            # Create lines for the daily production report
            for line in self.line_ids:
                self.env['oil.daily.production.line'].create({
                    'daily_production_id': daily_production.id,
                    'product_id': line.product_id.id,
                    'produced_qty': line.produced_qty,
                    'uom_id': line.uom_id.id,
                    'rate': line.rate,
                })
            
        return res
