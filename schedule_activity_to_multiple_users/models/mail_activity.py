# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj(odoo@cybrosys.com)
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
from odoo import api, fields, models


class MailActivity(models.Model):
    """Help to assign Scheduled activity to multiple users"""
    _inherit = 'mail.activity'

    assign_multiple_user_ids = fields.Many2many('res.users',
                                                string="Additional users",
                                                help='Select the other users '
                                                     'that you want to '
                                                     'schedule the activity')

    @api.model_create_multi
    def create(self, vals_list):
        """While we assign an activity to multiple users,
        it will create a new record corresponding to the assigned users"""
        res = super(MailActivity, self).create(vals_list)
        record = res.assign_multiple_user_ids
        for rec in record:
            self.create({
                'res_model_id': res.res_model_id[0].id,
                'res_id': res.res_id,
                'activity_type_id': res.activity_type_id[0].id,
                'date_deadline': res.date_deadline,
                'user_id': rec.id,
                'summary': res.summary,
            })
        return res

    @api.onchange('user_id')
    def _onchange_user_id(self):
        # Create a dictionary to map res_model to group references
        model_to_groups = {
            'sale.order': ("sales_team.group_sale_manager",
                           "sales_team.group_sale_salesman_all_leads"),
            'account.move': (
                "account.group_account_manager",
                "account.group_account_invoice"),
            'project.task': (
                "project.group_project_user", "project.group_project_manager"),
            'purchase.order': (
                "purchase.group_purchase_manager",
                "purchase.group_purchase_user"),
        }
        group_refs = model_to_groups.get(self.res_model, ())
        res = {'domain': {
            'assign_multiple_user_ids': [
                ('id', '!=', self.user_id.id),
                "|",
                ("groups_id", "=", self.env.ref(group_refs[0]).id),
                ("groups_id", "=", self.env.ref(group_refs[1]).id),
            ] if group_refs else [('id', '!=', self.user_id.id)]
        }}
        return res
