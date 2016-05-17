from openerp import models, fields,api,http,SUPERUSER_ID,_


class AutoFillWizard(models.TransientModel):
    _name = 'salon.auto_fill.wizard'

    name = fields.Char('Name')
    month = fields.Integer('Month')
    year = fields.Integer('Year')
    no_days = fields.Integer('No of Days')

    @api.one
    @api.onchange('month')
    def onchange_month(self):
        days = {1: 31, 2: 29, 3: 31,
                4: 30, 5: 31, 6: 30,
                7: 31, 8: 31, 9: 30,
                10: 31, 11: 30, 12: 31, }.get(self.month)
        if days:
            self.no_days = days

    @api.one
    def act_auto_fill(self):
        if self.name:
            month_name = self.name
        else:
            month_name = 'Untitled Month'+str(self.id)
        times_list = []
        for Each_Time in self.env['salon.period'].search([('day_id', '=', None)]):
            time_line_list = []
            for Each_Chair in self.env['salon.chair'].search([]):
                time_line_list.append((0, 0, {'chair_id': Each_Chair.id}))
            times_list.append((0, 0, {'name': Each_Time.name,
                                      'period_type': Each_Time.period_type,
                                      'off_reason': Each_Time.off_reason,
                                      'chair_lines': time_line_list}))
        days_list = []
        for day_count in range(1, self.no_days+1):
            day_line = {'name': day_count,
                        'period_lines': times_list}
            days_list.append((0, 0, day_line))

        month_values = {'name': month_name,
                        'month': self.month,
                        'year': self.year,
                        'day_lines': days_list}

        month_obj = self.pool.get('salon.month')
        month_obj.create(self._cr, self._uid, month_values)


    @api.one
    def close_auto_fill(self):
        pass

