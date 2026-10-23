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
from odoo import api, fields, models, _


class AccountMove(models.Model):
    """
    Inherit AccountMove class for add merge invoice action function,
    Method: action_merge_invoice(self):
        Create new wizard with selected records
    """
    _inherit = "account.move"

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """Displays partner name along with invoice name for merging purpose"""
        domain = domain or []
        res = super().name_search(name, domain, operator, limit)

        if self.env.context.get('display_invoice_with_partner'):
            records = self.browse([r[0] for r in res])
            return [
                (
                    rec.id,
                    f"{rec.name or ('Draft' if rec.state == 'draft' else '')} - "
                    f"{rec.partner_id.display_name or ''}"
                )
                for rec in records
            ]
        return res

    def action_merge_invoice(self):
        """ Method to create invoice merge wizard """
        merge_invoice = self.env['merge.invoice'].create({
            'invoice_ids': [fields.Command.set(self.ids)],
        })
        return {
            'name': _('Merge Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'merge.invoice',
            'view_mode': 'form',
            'res_id': merge_invoice.id,
            'target': 'new'
        }
