# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Linto CT (<https://www.cybrosys.com>)
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
import datetime
from odoo import models, fields


class CrmTargetAchievement(models.Model):
    _inherit = 'crm.team'

    def find_target(self, uid):
        """This function will return the target and achievement in a list,
        based on the user.
        input: id of the user
        output: list of dictionary with name and percentage """
        cr = self._cr
        today = datetime.date.today()
        begning = today.replace(day=1)
        target = 0
        tmp = {}
        achieved_total = 0
        if uid == 1:
            # admin will see the details of all users
            # taking all invoices
            for user in self.env['res.users'].search([]):
                target += user.target_sales_invoiced
            cr.execute("select ai.user_id, sum(ai.amount_untaxed) as total from account_invoice ai"
                       " where ai.state in ('open', 'paid') and ai.type='out_invoice' "
                       " and ai.date_invoice >= %s group by ai.user_id", (begning,))
            achieved = cr.dictfetchall()
            for i in achieved:
                rec = self.env['res.users'].browse(i['user_id'])
                tmp[rec.name] = i['total']
                achieved_total += i['total']

        else:
            # checking wheather this user is team lead or not
            team = self.env['crm.team'].search([('user_id', '=', self._uid)], limit=1)
            if team:
                # this user is team lead
                members = team.member_ids
                # taking team member's targets'
                for member in members:
                    target += member.target_sales_invoiced
                # taking his target
                target += self.env.user.target_sales_invoiced
                ids = members.ids
                ids.append(self._uid)
                cr.execute("select ai.user_id, sum(ai.amount_untaxed) as total from account_invoice ai"
                           " where ai.state in ('open', 'paid') and ai.type='out_invoice' "
                           " and ai.user_id in %s and ai.date_invoice >= %s group by ai.user_id",
                           (tuple(ids), begning))
                achieved = cr.dictfetchall()

                for i in achieved:
                    rec = self.env['res.users'].browse(i['user_id'])
                    tmp[rec.name] = i['total']
                    achieved_total += i['total']

            else:
                # this is just a user, not a team lead
                target += self.env.user.target_sales_invoiced
                cr.execute("select sum(amount_untaxed) as total from account_invoice "
                           " where state in ('open', 'paid') and ai.type='out_invoice' "
                           " and date_invoice >= %s and user_id=%s", (begning, self._uid))
                invoices = cr.dictfetchall()

                for i in invoices:
                    tmp[self.env.user.name] = i['total']
                    achieved_total += i['total']
        # checking the achieved amount is greater than target or not
        target_bal = target - achieved_total
        result = []

        if target_bal < 0:
            # achieved amount is greater than target
            for i in tmp:
                temp = {
                    'name': i + ":" + str(tmp[i]),
                    'percent': round((tmp[i] / target) * 100, 1),
                }
                result.append(temp)
            # taking the difference in target and achieved
            temp = {
                'name': 'Target Exceeded ' + ":" + str(-1*target_bal),
                'percent': round(-1 * (target_bal / target) * 100, 1),
            }
            result.append(temp)
        else:
            # achieved amount is lesser than or equal to  target
            for i in tmp:
                temp = {
                    'name': i + ":" + str(tmp[i]),
                    'percent': round((tmp[i] / target) * 100, 1),
                }
                result.append(temp)
            # taking the difference in target and achieved
            temp = {
                'name': 'Target Pending ' + ":" + str(target_bal),
                'percent': round((target_bal / target) * 100, 1),
            }
            result.append(temp)

        return result
