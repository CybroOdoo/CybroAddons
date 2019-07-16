# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2014-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jesni Banu(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _


class ResUsersInherit(models.Model):
    _inherit = 'res.users'

    employee_id = fields.Many2one('hr.employee',
                                  string='Related Employee', ondelete='restrict',
                                  help='Employee-related data of the user', auto_join=True)

    @api.model
    def create(self, vals):
        result = super(ResUsersInherit, self).create(vals)
        result['employee_id'] = self.env['hr.employee'].create({'name': result['name'],
                                                                'user_id': result['id'],
                                                                'address_home_id': result['partner_id'].id})
        return result
