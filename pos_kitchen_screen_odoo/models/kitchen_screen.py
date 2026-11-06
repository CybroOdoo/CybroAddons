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
#############################################################################
from odoo import api, fields, models


class KitchenScreen(models.Model):
    """Kitchen Screen model for the cook"""
    _name = 'kitchen.screen'
    _description = 'Pos Kitchen Screen'
    _rec_name = 'sequence'

    def _pos_shop_id(self):
        """Domain for the POS shop: restaurants not yet linked to a screen."""
        used_configs = self.search(
            [('pos_config_id', '!=', False)]).pos_config_id.ids
        domain = [('module_pos_restaurant', '=', True)]
        if used_configs:
            domain.append(('id', 'not in', used_configs))
        return domain

    sequence = fields.Char(readonly=True, default='New',
                           copy=False, help="Sequence of the kitchen screen")
    pos_config_id = fields.Many2one('pos.config', string='Allowed POS',
                                    domain=lambda self: self._pos_shop_id(),
                                    help="Allowed POS for kitchen")
    pos_categ_ids = fields.Many2many('pos.category',
                                     string='Allowed POS Category',
                                     help="Allowed POS categories "
                                          "for the corresponding POS")
    shop_number = fields.Integer(related='pos_config_id.id', string='Shop Number',
                                 help="ID of the POS")

    is_preparation_complete = fields.Boolean(
        string='Change Stage',
        default=False,
        help='Change the cooking stage when the preparation time is complete',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Used to create sequence"""
        for vals in vals_list:
            if vals.get('sequence', "New") == "New":
                vals['sequence'] = self.env['ir.sequence'].next_by_code(
                    'kitchen.screen') or "New"
        return super().create(vals_list)
