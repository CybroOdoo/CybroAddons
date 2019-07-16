# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Niyas Raphy(<http://www.cybrosys.com>)
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
from openerp import models


class LeaveApproval(models.Model):
    _inherit = 'hr.holidays'

    def holidays_validate(self, cr, uid, ids, context=None):
        res = super(LeaveApproval, self).holidays_validate(cr, uid, ids, context=context)
        ir_model_data = self.pool.get('ir.model.data')
        template_id = ir_model_data.get_object_reference(cr, uid, 'leave_approval_mail', 'email_template_leave')[1]
        self.pool.get('email.template').send_mail(cr, uid, template_id, ids[0], force_send=True, context=context)
        return res

    def holidays_refuse(self, cr, uid, ids, context=None):
        res = super(LeaveApproval, self).holidays_validate(cr, uid, ids, context=context)
        ir_model_data = self.pool.get('ir.model.data')
        template_id = ir_model_data.get_object_reference(cr, uid, 'leave_approval_mail', 'email_template_leave_rejection')[1]
        self.pool.get('email.template').send_mail(cr, uid, template_id, ids[0], force_send=True, context=context)
        return res
