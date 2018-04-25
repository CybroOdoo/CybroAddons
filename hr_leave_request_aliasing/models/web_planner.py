# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import api, models


class PlannerHrLeave(models.Model):
    """This class is used to activate web.planner feature in 'hr_leave_request_aliasing' module"""

    _inherit = 'web.planner'

    @api.model
    def _get_planner_application(self):
        planner = super(PlannerHrLeave, self)._get_planner_application()
        planner.append(['planner_hr_leave', 'Leave Planner'])
        return planner

    @api.model
    def _prepare_planner_hr_leave_data(self):
        alias_record = self.env.ref('hr_leave_request_aliasing.mail_alias_leave')
        return {
            'alias_domain': alias_record.alias_domain,
            'alias_name': alias_record.alias_name,
        }

