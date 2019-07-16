# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
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

from openerp import models, fields


class PopupReminder(models.Model):
    _name = 'popup.reminder'

    name = fields.Char(string='Title', required=True)
    model_name = fields.Many2one('ir.model', string="Model", required=True)
    model_field = fields.Many2one('ir.model.fields', string='Field',
                                  domain="[('model_id', '=',model_name),('ttype', 'in', ['datetime','date'])]",
                                  required=True)
    search_by = fields.Selection([('today', 'Today'),
                                  ('set_period', 'Set Period'),
                                  ('set_date', 'Set Date'), ],
                                 required=True, string="Search By")
    date_set = fields.Date(string='Select Date')
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
