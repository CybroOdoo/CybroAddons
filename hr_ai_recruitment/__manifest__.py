# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
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
{
    "name": "AI Recruiter",
    "version": "17.0.1.0.0",
    "category": "Human Resources/Recruitment",
    "summary": """AI-powered ATS scoring, CV analysis, and automated candidate shortlisting for Odoo Recruitment""",
    'description': """AI Recruitment Shortlist and ATS Score
     =====================================
     
     This module enhances the Odoo Recruitment application by integrating AI capabilities to automate and optimize the applicant screening process. It helps recruiters quickly identify and shortlist the most qualified candidates by analyzing their CVs against job requirements and custom criteria.
    
     Key Features:
     --------------
     * **AI-Powered ATS Score:** Calculates an Applicant Tracking System (ATS) score (out of 100) for applicants by sending the CV content and job details to an AI service.
     * **CV Content Extraction:** Automatically extracts text from CV attachments (PDF, etc.) using the PyMuPDF (`fitz`) library for accurate analysis.
     * **Custom Shortlist Criteria:** Configure reusable scoring criteria and weights to guide the AI's evaluation for different roles.
     * **Automated Mass Shortlisting:** Use a dedicated wizard on the Job form to filter and mass-shortlist applicants based on their ATS score.
     * **CV Score Summary:** Stores and displays the AI-generated score and a detailed summary of the CV evaluation directly on the Applicant form.
     * **Global Configuration:** Easily enable or disable the entire AI Shortlisting feature through the Recruitment settings.
     """,
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ['hr_recruitment', 'iap'],
    "data": [
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/hr_job_views.xml',
        'views/hr_applicant_views.xml',
        'views/hr_shortlist_views.xml',
        'wizard/hr_ai_shortlist_view.xml',
        'wizard/hr_ai_score_view.xml',
    ],
    'external_dependencies': {
        'python': ['pymupdf']
    },
    "images": ["static/description/banner.jpg"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": True,
}
