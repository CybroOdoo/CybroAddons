from openerp import models, fields,api
import datetime


class DoctorBenefit(models.Model):
    _name = 'med_marketing.doctor.line'

    name = fields.Char('Description')
    doctor_id = fields.Many2one('res.partner')
    account_id = fields.Many2one('account.account', 'Account')
    amt = fields.Float('Cost')
    exp_account = fields.Many2one('account.account', 'Expenses Account')
    state = fields.Selection([('unposted', 'Draft'), ('posted', 'Posted'), ], default="unposted")
    journal_id = fields.Many2one('account.journal', 'Journal')

    @api.one
    def post_confirm(self):
        self.state = 'posted'
        ref = 'DRX' + str(datetime.datetime.now().year) + str(self.id).zfill(4)
        num = 'DRX' + '/' + str(datetime.datetime.now().year) + '/' + str(self.id).zfill(4)
        if self.name == False:
            description = ''
        else:
            description = self.name
        j_lines_list = []
        j_lines_1 = {'name': description,
                     'partner_id': None,
                     'account_id': self.account_id.id,
                     'debit': 0.0,
                     'credit': self.amt,
                     }

        j_lines_list.append((0, 0, j_lines_1))
        j_lines_2 = {'name': description,
                     'partner_id': None,
                     'account_id': self.exp_account.id,
                     'debit': self.amt,
                     'credit': 0.0,
                     }

        j_lines_list.append((0, 0, j_lines_2))

        j_values = {'name': num,
                    'journal_id': self.journal_id.id,
                    'ref': ref,
                    'state': 'posted'
                        }

        j_values.update({'line_id': j_lines_list})
        j_obj = self.pool.get('account.move')
        j_obj.create(self._cr, self._uid, j_values)


class Doctors(models.Model):
    _inherit = 'res.partner'

    @api.one
    def get_current_id(self):
        return self.id

    def doctor_exp_btn(self, cr, uid, ids, context=None):
        created_domain = '[("doctor_id","in",'+str(self.get_current_id(cr, uid, ids, context))+')]'
        return {
            'name':'Doctor Expenses',
            'type': 'ir.actions.act_window',
            'res_model': 'med_marketing.doctor.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': created_domain,
        }

