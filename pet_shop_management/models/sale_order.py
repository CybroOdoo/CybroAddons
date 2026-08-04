# -*- coding: utf-8 -*-
##############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models, _


class SaleOrder(models.Model):
    """ Model for recording Pet sittings """
    _inherit = 'sale.order'

    pet_sittings = fields.Boolean(default=False, string="Pet Sittings",
                                  help="Identify as pet sitting.")

    def pet_sitting(self):
        """ Sitting Schedule wizards """
        self.pet_sittings = True
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': _('Pet Sitting Schedule'),
            'view_mode': 'form',
            'res_model': 'pet.sitting.schedule',
            'context': {'default_model_id': self.id,
                        'default_reference_id': self.id,
                        'default_schedule_description': self.name}
        }

    def action_return_meetings(self):
        """ Return the meetings view """
        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'name': _('Meetings'),
            'view_mode': 'calendar',
            'res_model': 'sitting.schedule'
        }


class SaleOrderLine(models.Model):
    """ Inheriting sale order line to add a new field """
    _inherit = 'sale.order.line'

    walker_sitting = fields.Many2one('hr.employee',
                                     domain="[('is_walker_sitters', '=', True)]",
                                     string='Walker/Sitting',
                                     help='Identifies as Pet walker')
