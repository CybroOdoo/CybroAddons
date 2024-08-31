"""Sticky notes"""
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
from odoo import models


class ResUsers(models.Model):
    """This class is used to return the sticky notes"""
    _inherit = 'res.users'

    def action_user_sticky_notes(self):
        """To return the sticky notes created by the user"""
        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'name': 'ASD',
            'view_type': 'tree',
            'view_mode': 'kanban',
            'res_model': 'stick.notes',
        }
