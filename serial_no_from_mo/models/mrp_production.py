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
from odoo import models


class MrpProduction(models.Model):
    """Manufacturing Production model for managing production orders.
        This model represents a production order and includes functionality for
         confirming the production, generating serial/lot numbers, and other
          related operations."""
    _inherit = "mrp.production"

    def _get_or_create_serial_sequence(self, product, mode, company):
        """ Retrieve or create ir.sequence using sudo to prevent AccessError,
        ensuring company-awareness, unique non-translatable codes, and avoiding
        unnecessary writes on every confirmation. """
        sequence_obj = self.env['ir.sequence'].sudo()
        if mode == 'global':
            params = self.env['ir.config_parameter'].sudo()
            code = 'mrp.production.sequence'
            name = 'Mrp Production'
            digit = params.get_int('serial_no_from_mo.mo_serial_digit', 0)
            prefix = params.get_str('serial_no_from_mo.mo_serial_prefix', '')
        else:
            code = f'mrp.production.product.{product.id}'
            name = f'Mrp Production - {product.default_code or product.id}'
            digit = product.product_tmpl_id.mo_serial_digit or 0
            prefix = product.product_tmpl_id.mo_serial_prefix or ''

        seq = sequence_obj.search([
            ('code', '=', code),
            ('company_id', 'in', [company.id, False]),
        ], limit=1)

        if not seq:
            seq = sequence_obj.create({
                'name': name,
                'implementation': 'standard',
                'code': code,
                'prefix': prefix,
                'padding': digit,
                'company_id': company.id,
            })
        else:
            vals = {}
            if seq.prefix != prefix:
                vals['prefix'] = prefix
            if seq.padding != digit:
                vals['padding'] = digit
            if vals:
                seq.write(vals)

        return seq

    def action_confirm(self):
        """ Confirm the production order and generate serial/lot numbers.
        This method checks product tracking and serial_selection configuration
        parameters to generate serial/lot numbers (globally or product-wise)
        without overwriting existing user-set lots, and generates appropriate
        counts according to product quantity."""
        params = self.env['ir.config_parameter'].sudo()
        is_enabled = params.get_bool('serial_no_from_mo.is_serial_selection')
        if is_enabled:
            mode = params.get_str('serial_no_from_mo.serial_selection', 'global')
            for rec in self:
                # Do not overwrite if lot/serial is already set by the user
                if rec.lot_producing_ids:
                    continue
                if rec.product_id.tracking in ['serial', 'lot']:
                    seq = self._get_or_create_serial_sequence(
                        rec.product_id, mode, rec.company_id
                    )
                    qty = int(rec.product_qty) if rec.product_id.tracking == 'serial' else 1
                    qty_to_generate = max(1, qty)
                    lots = self.env['stock.lot']
                    for _ in range(qty_to_generate):
                        serial_name = seq.next_by_id()
                        lot = self.env['stock.lot'].create({
                            'name': serial_name,
                            'product_id': rec.product_id.id,
                            'company_id': rec.company_id.id,
                        })
                        lots |= lot
                    rec.lot_producing_ids = lots
        return super().action_confirm()
