# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """Class for inherited model res partner. Contains required fields and
    functions of the module.
    Methods:
        load_views(self, views, options=None):
        Super load_views function to write into related
        user when opening the view"""
    _inherit = 'res.partner'

    related_user_id = fields.Many2one('res.users', readonly=True,
                                      string='Related User',
                                      help='The field contains the related'
                                           'of the partner if there is any')
    is_have_user = fields.Boolean(string='Have User',
                                  help='This field helps to check if there is'
                                       'any user related to the partner.')

    @api.model
    def load_views(self, views, options=None):
        """ Super load_views function to write into related user when opening
        the view.
            :param views: list of [view_id, view_type]
            :param dict options: a dict optional boolean flags, set to enable:
            :return: dictionary with fields_views, fields and optionally filters
        """
        res = super().load_views(views, options)
        for users in self.env['res.users'].search([]):
            for partner in self.search([]):
                if users.partner_id.id == partner.id:
                    partner.write({
                        'related_user_id': users,
                        'is_have_user': True
                    })
        return res
