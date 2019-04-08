from odoo import api, models, _


class PackingReportValues(models.AbstractModel):
    _name = 'report.employee_orientation.print_pack_template'

    @api.model
    def _get_report_values(self, docids, data=None):

        lst = []
        empl_obj = self.env['hr.employee'].search([('department_id', '=', data['dept_id'])])

        for line in empl_obj:
            lst.append({
                'name': line.name,
                'department_id': line.department_id.name,
                'program_name': data['program_name'],
                'company_name': data['company_name'],
                'date_to': data['date_to'],
                'program_convener': data['program_convener'],
                'duration': data['duration'],
                'hours': data['hours'],
                'minutes': data['minutes'],
            })

        return {
            'data': lst,
        }

