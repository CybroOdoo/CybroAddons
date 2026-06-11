# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
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
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """ Inherited Partner for generating unique sequence """
    _inherit = 'res.partner'

    unique_id = fields.Char(string='Unique Id', help="The Unique Sequence no",
                            readonly=True, default='/')

    @api.model_create_multi
    def create(self, vals_list):
        """ Super create function for generating sequence """
        res = super(ResPartner, self).create(vals_list)
        company = self.env.company.sudo()
        for record in res:
            if record.customer_rank > 0 and record.unique_id == '/':
                if company.next_code:
                    record.unique_id = company.next_code
                    record.name = '[' + str(company.next_code) + ']' + str(
                        record.name)
                    company.write({'next_code': company.next_code + 1})
                else:
                    record.unique_id = company.customer_code
                    record.name = '[' + str(company.customer_code) + ']' + str(
                        record.name)
                    company.write({'next_code': company.customer_code + 1})
        return res
