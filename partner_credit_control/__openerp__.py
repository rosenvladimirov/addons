# -*- coding: utf-8 -*-
##############################################################################
#
#    Partner Credit Control module for Odoo
#    Copyright (C) 2017 Rosen Vladimirov (vladimirov.rosen@gmail.com)
#    @author Rosen Vladimirov <vladimirov.rosen@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
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
    'name': 'Partner Credit Control',
    'version': '8.0.0.1.0',
    'category': 'Finance',
    'author': "Rosen Vladimirov,Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'summary': 'Small module to add options for credit control based on credit limit',
    'description': """
Partner Credit Control
======================

The module provaided:

* add new button for credit control
* add contrain in account invoice and pos order for credit limit

This module has been written by Rosen Vladimirov <vladimirov.rosen@gmail.com>.
    """,
    'author': 'Rosen Vladimirov',
    'depends': ['account_credit_control'],
    'data': [
            'views/res_partner_view.xml',
            'wizard/credit_control_agree.xml'
            ],
    'installable': True,
    'tests': [],
    'license': 'AGPL-3'
}
