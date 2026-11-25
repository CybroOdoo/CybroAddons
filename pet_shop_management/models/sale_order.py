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
from odoo import fields, models


class SaleOrder(models.Model):
    """ Model for recording Pet sittings """
    _inherit = 'sale.order'

    pet_sittings = fields.Boolean(
        default=False, string="Pet Sittings", copy=False,
        help="Indicates whether pet sitting schedules are linked with or "
             "scheduled from this sales order."
    )

    def pet_sitting(self):
        """ Sitting Schedule wizards """
        self.pet_sittings = True
        walker = self.order_line.filtered(
            lambda line: line.walker_sitting
        ).walker_sitting[:1]
        ctx = {
            'default_reference_id': self.id,
            'default_schedule_description': self.name,
        }
        if walker:
            ctx['default_walker_sitting_id'] = walker.id
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': self.env._('Pet Sitting Schedule'),
            'view_mode': 'form',
            'res_model': 'pet.sitting.schedule',
            'context': ctx,
        }

    def action_return_meetings(self):
        """ Return the meetings view """
        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'name': self.env._('Meetings'),
            'view_mode': 'calendar,list,form',
            'res_model': 'sitting.schedule',
            'domain': [('number_id', '=', self.id)],
            'context': {'default_number_id': self.id},
        }


class SaleOrderLine(models.Model):
    """ Inheriting sale order line to add a new field """
    _inherit = 'sale.order.line'

    walker_sitting = fields.Many2one(
        'hr.employee',
        domain="[('is_walker_sitters', '=', True)]",
        ondelete='set null',
        string='Walker/Sitter',
        help='Assigned pet walker or sitter employee responsible for '
             'delivering this service order line.'
    )
