# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class AccessRight(models.Model):
    """This class is used to detect, which all options want to hide from the
    specified group and model"""
    _name = 'access.right'
    _inherit = 'mail.thread'
    _description = 'Manage Modules Access Control'
    _rec_name = 'model_id'

    model_id = fields.Many2one('ir.model', ondelete='cascade',
                               required=True, string="Model",
                               help="Select the model")
    groups_id = fields.Many2one('res.groups',
                                string="Groups", help="Select the group")
    is_delete = fields.Boolean(string="Delete", help="Hide the delete option")
    is_export = fields.Boolean(string="Export",
                               help="Hide the 'Export All'"
                                    " option from list view")
    is_create_or_update = fields.Boolean(string="Create/Update",
                                         help="Hide the create option "
                                              "from list as well as form view")
    is_archive = fields.Boolean(string="Archive/UnArchive",
                                help="hide the archive option")
    restriction_type = fields.Selection([
        ('user', 'User Wise'),
        ('group', 'Group Wise')
    ], 'Restriction Type', required=True, default="group")
    user_id = fields.Many2one('res.users',
                              help="select the user")

    @api.model
    def hide_buttons(self):
        """This function contains a query  that detects which all options want
        to hide, in which model,and to which user groups"""
        access_right_rec = self.sudo().search_read([], ['model_id', 'is_delete',
                                                        'is_export',
                                                        'is_create_or_update',
                                                        'is_archive',
                                                        'restriction_type',
                                                        'user_id',
                                                        'groups_id'])
        for dic in access_right_rec:
            model = self.env['ir.model'].sudo().browse(dic['model_id'][0]).model
            if dic['restriction_type'] == "group":
                group_name = self.env['ir.model.data'].sudo().search([
                    ('model', '=', 'res.groups'),
                    ('res_id', '=', dic['groups_id'][0])
                ]).name

                module_name = self.env['ir.model.data'].sudo().search([
                    ('model', '=', 'res.groups'),
                    ('res_id', '=', dic['groups_id'][0])
                ]).module
            else:
                group_name=False
                module_name=False
            dic.update({
                'model': model,
                'group_name': group_name,
                'module': module_name,
                'restriction_type': dic['restriction_type'],
                'user':  dic['user_id']
            })
        return access_right_rec
