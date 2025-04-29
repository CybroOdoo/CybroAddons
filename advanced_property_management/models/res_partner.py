# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk  (odoo@cybrosys.com)
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


class ResPartner(models.Model):
    """A class that inherits the already existing model res partner"""
    _inherit = 'res.partner'

    blacklisted = fields.Boolean(string='Blacklisted', default=False,
                                 help='Is this contact a blacklisted contact '
                                      'or not')

    def create(self, vals_list):
        """Make partner to blacklist"""
        val = super(ResPartner, self).create(vals_list)
        val.blacklisted = True
        return val

    def action_add_blacklist(self):
        """Sets the field blacklisted to True"""
        self.blacklisted = True

    def action_remove_blacklist(self):
        """Sets the field blacklisted to False"""
        self.blacklisted = False
