# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class SaleOrderLine(models.Model):

    @api.one
    @api.depends('invoice_lines', 'invoice_lines.invoice_id',
                 'invoice_lines.quantity')
    def _compute_invoiced_qty(self):
        self.invoiced_qty = sum(self.invoice_lines.mapped('quantity'))

    @api.one
    @api.depends('invoice_lines', 'invoice_lines.invoice_id',
                 'invoice_lines.quantity', 'cancelled_qty')
    def _compute_fully_invoiced(self):
        self.fully_invoiced = \
            (self.invoiced_qty + self.cancelled_qty >= self.product_uom_qty)

    @api.one
    def _compute_all_invoices_approved(self):
        if self.invoice_lines:
            self.all_invoices_approved = \
                not any(inv_line.invoice_id.state in ['draft', 'cancel']
                        for inv_line in self.invoice_lines)
        else:
            self.all_invoices_approved = False

    _inherit = 'sale.order.line'

    invoiced_qty = fields.Float(
        compute='_compute_invoiced_qty',
        digits=dp.get_precision('Product Unit of Measure'),
        copy=False, store=True)

    cancelled_qty = fields.Float(
        string='Cancelled Quantity',
        digits=dp.get_precision('Product Unit of Measure'),
        copy=False)

    fully_invoiced = fields.Boolean(
        compute='_compute_fully_invoiced', copy=False, store=True)

    all_invoices_approved = fields.Boolean(
        compute='_compute_all_invoices_approved')

    date_order = fields.Datetime(
        string='Date order',
        related='order_id.date_order', readonly=True
    )

class SaleOrder(models.Model):

    _inherit = 'sale.order'

    @api.one
    def _compute_invoiced(self):
        self.invoiced = all((line.all_invoices_approved or
                             line.product_uom_qty == line.cancelled_qty) and
                            line.fully_invoiced
                            for line in self.order_line)

    #def _invoiced_search(self, cursor, user, obj, name, args, context=None):
    @api.model
    def _invoiced_search(self, domain, *args, **kwargs):
        if not len(args):
            return []
        clause = ''
        sale_clause = ''
        no_invoiced = False
        for arg in args:
            if (arg[1] == '=' and arg[2]) or (arg[1] == '!=' and not arg[2]):
                clause += 'AND inv.state = \'paid\' AND sale.invoiced = TRUE '
                sale_clause = ',  sale_order AS sale '
            else:
                clause += 'AND inv.state != \'cancel\' AND sale.state != \'cancel\'  AND inv.state <> \'paid\'  AND rel.order_id = sale.id AND sale.invoiced <> TRUE '
                sale_clause = ',  sale_order AS sale '
                no_invoiced = True

        cursor.execute('SELECT rel.order_id ' \
                'FROM sale_order_invoice_rel AS rel, account_invoice AS inv '+ sale_clause + \
                'WHERE rel.invoice_id = inv.id ' + clause)
        res = cursor.fetchall()
        if no_invoiced:
            cursor.execute('SELECT sale.id ' \
                    'FROM sale_order AS sale ' \
                    'WHERE sale.id NOT IN ' \
                        '(SELECT rel.order_id ' \
                        'FROM sale_order_invoice_rel AS rel) and sale.state != \'cancel\'')
            res.extend(cursor.fetchall())
        # check in virtual orders
        cursor.execute('SELECT sol.order_id ' \
                       'FROM sale_order_virtual AS vir, sale_order_line AS sol ' \
                       'WHERE vir.id = sol.virtual_sale_order_id AND vir.order_ids IN %s', (tuple([x[0] for x in res]),))
        res_vir = cursor.fetchall()
        if res_vir:
            res = res_vir
        if not res:
            return [('id', '=', 0)]
        _logger.debug("All orders with invoce relations %s" % res)
        return [('id', 'in', [x[0] for x in res])]

    invoiced = fields.Boolean(compute='_compute_invoiced', string='Paid', fnct_search=_invoiced_search, help="It indicates that an invoice has been paid.")

    @api.model
    def _prepare_inv_line(self, account_id, order_line):
        res = super(SaleOrder, self).\
            _prepare_inv_line(account_id, order_line)
        ctx = self.env.context.copy()
        if ctx.get('partial_quantity_lines'):
            partial_quantity_lines = ctx.get('partial_quantity_lines')
            if order_line.id in partial_quantity_lines:
                res.update({'quantity':
                            partial_quantity_lines.get(order_line.id)})
        return res

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _order_lines_from_invoice(self):
        res = super(AccountInvoice, self).invoice_validate(self.ids)
        sale_order_line_obj = self.env['sale.order.line']
        sol_ids = sale_order_line_obj.with_context(self._context)._order_lines_from_invoice(self.ids)
        for so_line in sale_order_line_obj.browse(sol_ids):
            total_quantity = so_line.invoiced_qty + so_line.cancelled_qty
            if total_quantity < so_line.product_uom_qty:
                so_line.invoiced = False
        return res
