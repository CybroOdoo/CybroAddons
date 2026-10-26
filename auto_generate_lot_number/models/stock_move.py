# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com/>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com/>)
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
from odoo import models


class StockMove(models.Model):
    """Inherited StockMove class to auto generate lot and serial numbers"""
    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """Super the function to update the lot/serial number in stock.move.line"""
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        company = self.company_id or self.env.company
        auto_generate = company.check_auto_generate or self.env[
            'ir.config_parameter'
        ].sudo().get_bool('auto_generate_lot_number.is_auto_generate')

        is_tracked = self.product_id.tracking in ('lot', 'serial')
        has_no_lot = not vals.get('lot_id') and not vals.get('lot_name')
        if auto_generate and self.picking_code == 'incoming' and is_tracked and has_no_lot:
            serial_number_type = self.env['ir.config_parameter'].sudo().get_str(
                'auto_generate_lot_number.serial_number_type'
            )
            prefix = self.env['ir.config_parameter'].sudo().get_str(
                'auto_generate_lot_number.prefix', default=''
            ) or ''
            digits = self.env['ir.config_parameter'].sudo().get_int(
                'auto_generate_lot_number.digits', default=0
            )
            if serial_number_type == 'global':
                seq_code = 'auto.generate.lot.sequence'
                sequence = self.env['ir.sequence'].sudo().search(
                    [('code', '=', seq_code)], limit=1
                )
                if not sequence:
                    sequence = self.env['ir.sequence'].sudo().search(
                        [('code', '=', 'res.config.code')], limit=1
                    )
                if not sequence:
                    sequence = self.env['ir.sequence'].sudo().create({
                        'name': 'Auto Generate Lot Sequence',
                        'code': seq_code,
                        'company_id': company.id,
                    })
                lot_name = sequence.next_by_code(sequence.code) or '1'
                lot_name = f"{prefix}{lot_name.zfill(digits)}"
                vals['lot_name'] = lot_name
            elif serial_number_type == 'product':
                lot_name = self.product_id.product_tmpl_id._number_next_actual()
                if lot_name:
                    vals['lot_name'] = lot_name
        return vals

    def action_show_details(self):
        """Used to override the 'view_stock_move_operations' view"""
        res = super().action_show_details()
        auto_generate = self.env['ir.config_parameter'].sudo().get_bool(
            'auto_generate_lot_number.is_auto_generate'
        )
        if auto_generate:
            view = self.env.ref('auto_generate_lot_number.view_stock_move_operations')
            res.update({
                'views': [(view.id, 'form')],
                'view_id': view.id,
            })
        return res