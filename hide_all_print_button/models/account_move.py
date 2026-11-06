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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models
from .hide_print_tools import hide_print_buttons


class AccountMove(models.Model):
    """ Class for inherited model account.move.
    Methods:
        get_views(self, views, options=None):
            Function to make print button invisible according to the boolean
            field in res.users.
    """
    _inherit = 'account.move'

    @api.model
    def get_views(self, views, options=None):
        """ Function to make print button invisible according to the
            boolean field in res.users.
            views(list): List of views and ids
            options(dict): Dictionary of action_id,load_filters,and toolbar
            boolean:Returns true.
        """
        res = super().get_views(views, options)
        if self.env.user.hide_invoicing_print:
            hide_print_buttons(self.env, res)
        return res
