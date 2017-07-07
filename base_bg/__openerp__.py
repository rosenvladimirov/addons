# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
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
    'name': 'Base bg',
    'version': '1.0',
    'category': 'Hidden',
    'description': """
The special dummy module for all fixes included in,
core of oddo kernal, account, sale, purhase module.
if  you  have  this module in your instalations is
need  to  fix  all  core  modules  to  work system 
corectly.
===================================================
""",
    'author': 'Rosen Vladimirov',
    'maintainer': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'depends': [
               'l10n_bg_expert',
            ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
