.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

================
Base report xlsx
================

This module provides a basic report class to generate xlsx report.

Installation
============

Make sure you have ``xlsxwriter`` Python module installed::

$ pip install xlsxwriter

Usage
=====

An example of XLSX report for partners:

A python class ::

    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx

    class PartnerXlsx(ReportXlsx):
    
        def generate_xlsx_report(self, workbook, data, partners):
            for obj in partners:
                report_name = obj.name
                # One sheet by partner
                sheet = workbook.add_worksheet(report_name[:31])
                bold = workbook.add_format({'bold': True})
                sheet.write(0, 0, obj.name, bold)


    PartnerXlsx('report.res.partner.xlsx',
                'res.partner')

To manipulate the ``workbook`` and ``sheet`` objects, refer to the
`documentation <http://xlsxwriter.readthedocs.org/>`_ of ``xlsxwriter``.

A report XML record ::

    <report 
        id="partner_xlsx"
        model="res.partner"
        string="Print to XLSX"
        report_type="xlsx"
        name="res.partner.xlsx"
        file="res.partner.xlsx"
        attachment_use="False"
    />

