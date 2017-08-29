# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo Bulgaria Accounting, Open Source Accounting and Invoiceing Module
#    Copyright (C) 2016 Rosen Vladimirov, Prodax LTD
#    (vladimirov.rosen@gmail.com, http://www.prodax.bg)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Bulgaria - Accounting expert version",
    "version" : "1.0",
    "author" : "Rosen Vladimirov",
    "website": "http://www.prodax.bg",
    "category" : "Localization/Account Charts",
    "depends" : ['account','account_chart','base_vat'],
    "description": """
This is the module to manage the Reports, Fiscal Position for fiscal printer.
=============================================================================

Bulgarian accounting chart and localization.
    """,
    'conflicts': ['l10n_bg_expert'],
    'depends': [
        'account',
        'base_vat',
        'base_iban',
        'account_chart',
        'l10n_multilang',
        'report_qweb_element_page_visibility',
        'partner_identification_bg',
        'report',
        'partner_fr_person'
    ],
    "demo" : [],
    "data" : [
              #'views/account_report.xml',
              'views/layouts.xml',
              'views/report_invoice.xml',
              'views/account_view.xml'
              ],
    "license": "AGPL-3",
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
