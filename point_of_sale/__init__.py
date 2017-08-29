# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import account_bank_statement
import controllers
import point_of_sale
import report
import res_users
import res_partner
import wizard

def pre_init_hook(cr):
    cr.execute("select count(table_name) from information_schema.columns where table_name = 'pos_order' and column_name = 'invoice_id'")
    if cr.fetchall():
        migrate_from_single_invoice(cr)
    cr.execute("select count(table_name) from information_schema.columns where table_name = 'pos_order' and column_name = 'picking_id'")
    if cr.fetchall():
        migrate_from_single_picking(cr)

def migrate_from_single_invoice(cr):
    cr.execute("insert into pos_order_invoice_rel (order_id, invoice_id) select id, invoice_id from pos_order where invoice_id is not null")

def migrate_from_single_picking(cr):
    cr.execute("insert into pos_order_picking_rel (order_id, picking_id) select id, picking_id from pos_order where picking_id is not null")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
