# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Renjith (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ERPDashboard(models.Model):
    """ Class to get all the required data for the dashboard """
    _name = "erp.dashboard"
    _description = "Education ERP Dashboard"

    @api.model
    def erp_data(self):
        """ Function to get the datas like number of application, number of
        students, number of faculties, number of amenities and number of
        exams """
        return {
            'applications': self.env['education.application'].search_count([]),
            'students': self.env['education.student'].search_count([]),
            'faculties': self.env['education.faculty'].search_count([]),
            'amenities': self.env['education.amenities'].search_count([]),
            'exams': self.env['education.exam'].search_count([]),
        }

    @api.model
    def get_all_applications(self):
        """ Function to get count of applications in each academic year """
        years = self.env['education.application'].search([]).mapped(
            'academic_year_id')
        application_count_dict = {
            year.name: self.env['education.application'].search_count(
                [('academic_year_id', '=', year.name)]) for year in years}
        return application_count_dict

    @api.model
    def get_rejected_accepted_applications(self):
        """ Function to get count of all accepted and rejected applications """
        application_dict = {}
        academic_year_date = 0
        academic_year_year = ''
        academic_year = self.env['education.academic.year'].search([])
        for years in academic_year:
            academic_year_date = years.ay_end_date
            academic_year_year = years.name
        for year in academic_year:
            if academic_year_date < year.ay_end_date:
                academic_year_date = year.ay_end_date
                academic_year_year = year.name
        rejected_applications = self.env['education.application'].search_count(
            [('state', '=', 'reject'),
             ('academic_year_id', '=', academic_year_year)])
        accepted_applications = self.env['education.application'].search_count(
            [('state', '=', 'done'),
             ('academic_year_id', '=', academic_year_year)])
        application_dict.update(
            {'Done': accepted_applications, 'Reject': rejected_applications})
        return application_dict

    @api.model
    def get_exam_result(self):
        """ Function to get total exam result """
        exam_result_dict = {}
        pass_count = self.env['results.subject.line'].search_count(
            [('pass_or_fail', '=', True)])
        fail_count = self.env['results.subject.line'].search_count(
            [('pass_or_fail', '=', False)])
        exam_result_dict.update({'Pass': pass_count, 'Fail': fail_count})
        return exam_result_dict

    @api.model
    def get_attendance(self):
        """ Function to get total attendance """
        attendance_dict = {}
        absents = self.env['education.attendance.line'].search_count(
            [('date', '=', fields.Date.today()), ('full_day_absent', '=', 1)])
        total = self.env['education.student'].search_count([])
        presents = total - absents
        attendance_dict.update({'Presents': presents, 'Absents': absents})
        return attendance_dict

    @api.model
    def get_student_strength(self):
        """ Function to get class wise student strength """
        classes = self.env['education.class.division'].search([])
        class_wise_dict = {
            clas.name: self.env['education.student'].search_count(
                [('class_id', '=', clas.id)]) for clas in classes}
        return class_wise_dict

    @api.model
    def get_average_marks(self):
        """ Function to get class wise average marks """
        class_average_mark_dict = {}
        classes = self.env['education.class.division'].search([])
        for clas in classes:
            all_students = self.env['education.student'].search(
                [('class_id', '=', clas.id)])
            if all_students:
                class_mark_list = [sum(
                    self.env['education.exam.results'].search(
                        [('student_id', '=', student.id)]).mapped(
                        'total_mark_scored')) for student in all_students]
                count = len(class_mark_list)
                total_marks = sum(class_mark_list)
                average_mark = total_marks / count
                class_average_mark_dict.update({clas.name: average_mark})
        return class_average_mark_dict

    @api.model
    def get_academic_year(self):
        """ Function to get the academic year """
        academic_dict = {year.id: year.name for year in
                         self.env['education.academic.year'].search([])}
        return academic_dict

    @api.model
    def get_academic_year_exam_result(self, *args):
        """ Function to get exam results in each academic year """
        academic_exam_result_dict = {}
        academic_pass_count = self.env['results.subject.line'].search_count(
            [('academic_year.id', '=', *args), ('pass_or_fail', '=', True)])
        academic_fail_count = self.env['results.subject.line'].search_count(
            [('academic_year.id', '=', *args), ('pass_or_fail', '=', False)])
        academic_exam_result_dict.update(
            {'Pass': academic_pass_count, 'Fail': academic_fail_count})
        return academic_exam_result_dict

    @api.model
    def get_classes(self):
        """ Function to get the classes """
        class_dict = {clas.id: clas.name for clas in
                      self.env['education.class.division'].search([])}
        return class_dict

    @api.model
    def get_class_attendance_today(self, *args):
        """ Function to get class wise attendance """
        class_attendance_dict = {}
        class_absents = self.env['education.attendance.line'].search_count(
            [('division_id.id', '=', *args),
             ('date', '=', fields.Date.today()),
             ('full_day_absent', '=', 1)])
        class_total = self.env['education.student'].search_count(
            [('class_id.id', '=', *args)])
        class_presents = class_total - class_absents
        class_attendance_dict.update(
            {'Presents': class_presents, 'Absents': class_absents})
        return class_attendance_dict
