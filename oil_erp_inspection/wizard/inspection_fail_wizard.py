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
from odoo import api, fields, models
from odoo.tools.translate import _


class OilInspectionFailWizard(models.TransientModel):
    """Handles scrap creation when an inspection fails."""
    _name = 'oil.inspection.fail.wizard'
    _description = 'Inspection Fail Wizard'

    inspection_id = fields.Many2one(
        'oil.inspection.order',
        string='Inspection',
        required=True,
        help="Select the inspection.")
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='inspection_id.product_id',
        help="Select the product.")
    quantity = fields.Float(
        string='Original Quantity',
        related='inspection_id.production_id.product_qty',
        help="Enter the original Quantity.")
    scrap_qty = fields.Float(
        string='Scrap Quantity',
        required=True,
        help="Enter the scrap Quantity.")
    scrap_reason = fields.Char(
        string='Scrap Reason',
        required=True,
        help="Enter the scrap Reason.")
    scrap_location_id = fields.Many2one(
        'stock.location',
        string='Scrap Location',
        required=True,
        help="Select the scrap Location.")

    @api.model
    def default_get(self, fields_list):
        """
        Populate default values for the scrap wizard from the active inspection order.
        """
        res = super().default_get(fields_list)
        if self._context.get('active_id'):
            res['inspection_id'] = self._context.get('active_id')
            inspection = self.env['oil.inspection.order'].browse(
                self._context.get('active_id'))
            res['scrap_qty'] = inspection.production_id.product_qty
            res['scrap_reason'] = _('Inspection failed: %s') % inspection.name

            # Use Odoo's default scrap location logic
            scrap_defaults = self.env['stock.scrap'].default_get(
                ['scrap_location_id'])
            if scrap_defaults.get('scrap_location_id'):
                res['scrap_location_id'] = scrap_defaults['scrap_location_id']
        return res

    def action_scrap(self):
        """
           Create a stock scrap record from the inspection and mark the inspection as failed.
           Validates the scrap entry and links it to the inspection order before closing the wizard.
        """
        self.ensure_one()
        # Create stock scrap using the user-selected or default scrap location
        scrap_vals = {
            'product_id': self.product_id.id,
            'scrap_qty': self.scrap_qty,
            'product_uom_id': self.product_id.uom_id.id,
            'production_id': self.inspection_id.production_id.id,
            'scrap_location_id': self.scrap_location_id.id,
            'origin': self.inspection_id.name,
        }

        scrap = self.env['stock.scrap'].create(scrap_vals)
        scrap.action_validate()

        # Update inspection state and link scrap
        self.inspection_id.write({
            'state': 'failed',
            'scrap_id': scrap.id,
        })
        return {'type': 'ir.actions.act_window_close'}
