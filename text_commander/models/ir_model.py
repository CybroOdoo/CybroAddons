# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#  Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ramees Jaman KT (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, models


class IrModel(models.Model):
    """ Class to check the model and get the record values as specified by
    the user """
    _inherit = 'ir.model'

    @api.model
    def check_model(self, data):
        """ Check model from frontend"""
        self.env.cr.execute("""select model,name from ir_model
                    where lower(name->>'en_US')=lower('%s') limit 1""" % data)
        model = self.env.cr.dictfetchall()
        return model

    @api.model
    def get_records(self, data):
        """ Function for fetching record from database"""
        if data['regex'] == 1:
            if self.env[data['model']].fields_get('name')['name']['translate']:
                self.env.cr.execute(
                    """SELECT id FROM %s WHERE lower(name->>'en_US')
                    LIKE '%%%s%%'""" % (
                        data['model'].replace('.', '_'),
                        data['record'].lower()))
                record = [d['id'] for d in self.env.cr.dictfetchall()]
                return record
            else:
                self.env.cr.execute(
                    """SELECT id FROM %s WHERE lower(name) LIKE '%%%s%%'""" % (
                        data['model'].replace('.', '_'),
                        data['record'].lower()))
                record = [d['id'] for d in self.env.cr.dictfetchall()]
                return record
        if data['regex'] == 2:
            if data['field_type'] == 'many2one':
                self.env.cr.execute(
                    """SELECT id FROM %s WHERE lower(name) LIKE '%%%s%%'""" % (
                        data['field_relation'].replace('.', '_'),
                        data['field_string'].lstrip().lower()))
                record = [d['id'] for d in self.env.cr.dictfetchall()]
                return self.env[data['model']].search(
                    [(data['field'], 'in', record)]).ids
            elif data['field_type'] == 'selection':
                for state, label in self._get_selection_values(data):
                    if data['field_string'].lstrip().lower() == label.lower():
                        data['field_string'] = state
                return self.env[data['model']].search(
                    [(data['field'], '=', data['field_string'])]).ids
            else:
                self.env.cr.execute(
                    """SELECT id from %s where lower(%s) like '%%%s%%'""" % (
                        data['model'].replace('.', '_'), data['field'],
                        data['field_string'].lstrip().lower()))
                record = [rec['id'] for rec in self.env.cr.dictfetchall()]
                return record

    def _get_selection_values(self, data):
        """ Function for getting selection values"""
        return \
            self.env[data['model']].fields_get(data['field'])[data['field']][
                'selection']

    @api.model
    def check_fields_model(self, data):
        """Function for checking field of a model"""
        string = ""
        for rec in range(len(data['field_string'])):
            if rec != 0:
                string += " " + data['field_string'][rec]
            else:
                string += data['field_string'][rec]
            self.env.cr.execute(
                """select name ,ttype,relation from ir_model_fields where
                model = '%s' and lower(field_description->>'en_US') =
                lower('%s') limit 1""" % (
                    data['model'], string))
            res = self.env.cr.dictfetchall()
            if res:
                res[0]['del'] = string
                return res
            elif rec == len(data['field_string']) - 1:
                res = []
                return res
