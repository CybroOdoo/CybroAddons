# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2008-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from lxml import etree


class ColorPickerCustom(models.Model):
    _name = 'note.color'

    name = fields.Char(string="Criteria", help="Name for this date interval")
    color_note = fields.Selection(
        [('0', 'White'), ('1', 'Grey'), ('2', 'Orange'), ('3', 'Light yellow'), ('4', 'Light green'),
         ('5', 'Green'), ('6', 'Sky Blue'), ('7', 'Blue'), ('8', 'Purple'),
         ('9', 'Pink')], required=True, default='0', help="Colour of the record")

    start_interval = fields.Integer(string="Lower limit", default='1', required=True,
                                    help="Starting interval should be a integer (Number of days)")
    end_interval = fields.Integer(string="Upper limit", default='2', required=True,
                                  help="End interval  should be a integer (Number of days)")


class NoteConfiguration(models.Model):
    _name = 'note.config'
    _rec_name = "default_magic_color"

    default_magic_color = fields.Selection(
        [('0', 'White'), ('1', 'Grey'), ('2', 'Orange'), ('3', 'Light yellow'), ('4', 'Light green'),
         ('5', 'Green'), ('6', 'Sky Blue'), ('7', 'Blue'), ('8', 'Purple'),
         ('9', 'Pink')], string="Default", required=True, default='0',
        help="This color will be set to the records if no date interval record is found"
             "By default records are coloured to white")

    not_in_interval = fields.Selection(
        [('0', 'White'), ('1', 'Grey'), ('2', 'Orange'), ('3', 'Light yellow'), ('4', 'Light green'),
         ('5', 'Green'), ('6', 'Sky Blue'), ('7', 'Blue'), ('8', 'Purple'),
         ('9', 'Pink')], string="If Not inside the Interval", required=True, default='1',
        help="This color will be set to the records which doesn't come under any defined interval stages."
             "By default the records are coloured to Grey")

    deadline_cross = fields.Selection(
        [('0', 'White'), ('1', 'Grey'), ('2', 'Orange'), ('3', 'Light yellow'), ('4', 'Light green'),
         ('5', 'Green'), ('6', 'Sky Blue'), ('7', 'Blue'), ('8', 'Purple'),
         ('9', 'Pink')], string="After deadline ", required=True, default='8',
        help="This color will be set to the notes once they cross the dead date")


class NoteField(models.Model):
    _name = 'note.note'
    _inherit = 'note.note'

    dead_date = fields.Date(string="Dead Date", default=fields.Date.today(), required=True,
                            help="The deadline of this note:: Activate developer mode to  set color")

    def fields_view_get(self, cr, uid, view_id=None, view_type='kanban', context=None, toolbar=False, submenu=False):
        ret_val = super(NoteField, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type, context=context,
            toolbar=toolbar, submenu=submenu)
        doc = etree.XML(ret_val['arch'])
        current_date = fields.datetime.now()
        value = self.pool.get('note.color').search(cr, uid, [], context=None)
        if len(value) == 0:
            note = self.pool.get('note.note').search(cr, uid, [], context=None)
            for each in note:
                obj = self.pool.get('note.note').browse(cr, uid, each)
                obj2 = self.pool.get('note.config').browse(cr, uid, 1)
                col_default = obj2.default_magic_color
                obj.write({'color': col_default})
        else:
            note = self.pool.get('note.note').search(cr, uid, [], context=None)
            for each in note:
                obj = self.pool.get('note.note').browse(cr, uid, each)
                fmt = '%Y-%m-%d'
                date_dead = datetime.strptime(obj.dead_date, fmt)
                if current_date > date_dead:
                    obj2 = self.pool.get('note.config').browse(cr, uid, 1)
                    dead_line_cross = obj2.deadline_cross
                    obj.write({'color': dead_line_cross})
                else:
                    r = relativedelta(date_dead, current_date)
                    for i in value:
                        flag = 0
                        obj1 = self.pool.get('note.color').browse(cr, uid, i)
                        st_date = obj1.start_interval
                        end_date = obj1.end_interval
                        if st_date < r.days < end_date:
                            col = obj1.color_note
                            obj.write({'color': col})
                            flag += 1
                    if flag == 0:
                        obj3 = self.pool.get('note.config').browse(cr, uid, 1)
                        col_not_in_range = obj3.not_in_interval
                        obj.write({'color': col_not_in_range})
        for node in doc.xpath("//ul[@class='oe_kanban_colorpicker']"):
            ret_val['arch'] = etree.tostring(doc)
        return ret_val
