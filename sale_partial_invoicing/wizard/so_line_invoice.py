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

from __future__ import division
from openerp import models, fields, api, exceptions
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

import logging
_logger = logging.getLogger(__name__)


class SaleLineInvoice(models.TransientModel):

    _inherit = 'sale.order.line.make.invoice'

    line_ids = fields.One2many('sale.order.line_invoice.line',
                               'wizard_id', string='Lines')

    @api.model
    def default_get(self, fields):
        ctx = self.env.context.copy()
        so_ids = ctx.get('active_ids', [])
        so_line_obj = self.env['sale.order.line']
        lines = []
        for so_line in so_line_obj.browse(so_ids):
            max_quantity = so_line.product_uom_qty - so_line.invoiced_qty -\
                so_line.cancelled_qty
            lines.append({
                'so_line_id': so_line.id,
                'product_qty': max_quantity,
                'invoiced_qty': max_quantity,
                'price_unit': so_line.price_unit,
            })
        defaults = super(SaleLineInvoice, self).default_get(fields)
        defaults['line_ids'] = lines
        return defaults

    @api.multi
    def make_invoices(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        changed_lines = {}
        ctx['active_ids'] = []
        not_invoiced_lines = self.env['sale.order.line']
        invoiced_lines = self.env['sale.order.line']
        for line in self.line_ids:
            if line.invoiced_qty > line.product_qty:
                raise exceptions.Warning(
                    _("""Quantity to invoice is greater
                    than available quantity"""))
            ctx['active_ids'].append(line.so_line_id.id)
            changed_lines[
                line.so_line_id.id
            ] = line.invoiced_qty
            if line.so_line_id.fully_invoiced:
                invoiced_lines += line.so_line_id
            else:
                not_invoiced_lines += line.so_line_id
        #not_invoiced_lines.write({'invoiced': False})
        #invoiced_lines.write({'invoiced': True})
        ctx.update({'partial_quantity_lines': changed_lines})
        _logger.info("Make invoice %s" % ctx)
        res = super(SaleLineInvoice, self.with_context(ctx))\
            .make_invoices()
        #so_lines = self.env['sale.order.line'].browse(changed_lines.keys())
        #for so_line in so_lines:
        #    if so_line.invoiced_qty != so_line.product_uom_qty:
        #        so_line.invoiced = False
        return res


class SaleLineInvoiceLine(models.TransientModel):

    _name = 'sale.order.line_invoice.line'

    so_line_id = fields.Many2one('sale.order.line', 'Sale order line',
                                 readonly=True)
    product_qty = fields.Float(
        'Quantity', digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    price_unit = fields.Float(related='so_line_id.price_unit',
                              string='Unit Price', readonly=True)
    invoiced_qty = fields.Float(
        string='Quantity to invoice',
        digits=dp.get_precision('Product Unit of Measure'))
    wizard_id = fields.Many2one('sale.order.line_invoice', 'Wizard')
