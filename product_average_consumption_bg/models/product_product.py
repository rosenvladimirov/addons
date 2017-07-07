# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product - Average Consumption Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
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

import time
import datetime
from openerp import models, fields, api
from openerp.tools.float_utils import float_round
import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    # Columns Section
    product_consumption_ids = fields.Many2many(
        comodel_name='product.consumption', inverse_name='product_id',
        string='Average consumption')
    average_consumption = fields.Float(
        compute='_average_consumption',
        string='Average Consumption', multi='average_consumption')
    displayed_average_consumption = fields.Float(
        compute='_displayed_average_consumption',
        string='Average Consumption')
    total_consumption = fields.Float(
        compute='_average_consumption',
        string='Total Consumption', multi='average_consumption')
    nb_days = fields.Integer(
        compute='_average_consumption',
        string='Number of days for the calculation',
        multi='average_consumption',
        help="""The calculation will be done according to Calculation Range"""
        """ field or since the first stock move of the product if it's"""
        """ more recent""")
    consumption_calculation_method = fields.Selection(
        related='product_tmpl_id.consumption_calculation_method')
    display_range = fields.Integer(
        related='product_tmpl_id.display_range')
    calculation_range = fields.Integer(
        related='product_tmpl_id.calculation_range')

    # Private Function Section
    @api.model
    def _min_date(self, product_id):
        query = """SELECT to_char(min(date), 'YYYY-MM-DD') \
                from stock_move where product_id = %s""" % (product_id)
        cr = self.env.cr
        _logger.info("Select: %s" % query)
        cr.execute(query)
        results = cr.fetchall()
        return results and results[0] and results[0][0] \
            or time.strftime('%Y-%m-%d')

    # Fields Function Section
    @api.depends(
        'consumption_calculation_method', 'calculation_range')
    @api.multi
    def _average_consumption(self):
        ctx = dict(self.env.context).copy()
        cr, uid = self.env.cr, self.env.uid
        location_ids = []
        consumtion_obj = self.env['product.consumption']
        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')
        res_users_obj = self.env['res.users']
        user_brw = res_users_obj.browse(uid)
        warehouse = user_brw.default_section_id.default_warehouse
        if warehouse:
            ctx.update({'warehouse': warehouse.id})
        if ctx.get('warehouse', False):
            if isinstance(ctx['warehouse'], (int, long)):
                wids = [ctx['warehouse']]
            elif isinstance(ctx['warehouse'], basestring):
                domain = [('name', 'ilike', ctx['warehouse'])]
                if ctx.get('force_company', False):
                    domain += [('company_id', '=', ctx['force_company'])]
                wids = warehouse_obj.search(cr, uid, domain, context=ctx)
            else:
                wids = ctx['warehouse']
        else:
            wids = warehouse_obj.search(cr, uid, [], context=ctx)
        for w in warehouse_obj.browse(cr, uid, wids, context=ctx):
            location_ids.append(w.view_location_id.id)
        #_logger.info("Teke ctx %s:%s" % (ctx, location_ids))
        for product in self:
            if product.consumption_calculation_method == 'moves':
                for location in location_obj.browse(cr, uid, location_ids, context=self.env.context):
                    out_qty = 0
                    move_out_id = consumtion_obj.search([
                                        ('location_id', "=", location.id),
                                        ('product_id', '=', product.id)])
                    if move_out_id:
                        for consumtion in consumtion_obj.browse(move_out_id.id):
                            _logger.info("Consumption %s:%s" % (consumtion,move_out_id))
                            out_qty += consumtion.outgoing_qty
                            nb_days = consumtion.nb_days
                        #product._average_consumption_moves()
                        outgoing_qty = float_round(
                            out_qty,
                            precision_rounding=product.uom_id.rounding)
                        product.average_consumption = (
                            nb_days and
                            (outgoing_qty / nb_days) or False)
                        product.total_consumption = outgoing_qty or False
                        product.nb_days = nb_days or False
                        self._displayed_average_consumption()

    # Action section
    @api.model
    def run_product_consumption(self):
        # This method is called by the cron task
        #team_obj = self.env['crm.case.section']
        #context = {}
        #for team in team_obj.browse()
        #    context['warehouse'] = team.default_warehouse
        #    break
        products = self.env['product.product'].search([
            '|', ('active', '=', True),
            ('active', '=', False)])
        products._average_consumption_moves()

    #@api.onchange('calculation_range')
    @api.model
    def _average_consumption_moves(self):
        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')
        consumption_obj = self.pool.get('product.consumption')
        cr, uid = self.env.cr, self.env.uid
        ctx = dict(self.env.context).copy()
        location_ids = []
        domain_move_out = [('state', 'not in', ('cancel', 'draft'))] + self._get_domain_dates() + \
                          [('product_id', 'in', self.ids)] + \
                          [('location_dest_id.usage', '=', 'customer'), ('location_id.usage', '=', 'internal')]
        if ctx.get('owner_id'):
            owner_domain = ('restrict_partner_id', '=', ctx['owner_id'])
            domain_move_out.append(owner_domain)
        if ctx.get('location', False):
            if isinstance(ctx['location'], (int, long)):
                location_ids = [ctx['location']]
            elif isinstance(ctx['location'], basestring):
                domain = [('complete_name','ilike',ctx['location'])]
                if ctx.get('force_company', False):
                    domain += [('company_id', '=', ctx['force_company'])]
                location_ids = location_obj.search(cr, uid, domain, context=ctx)
            else:
                location_ids = ctx['location']
        else:
            if ctx.get('warehouse', False):
                if isinstance(ctx['warehouse'], (int, long)):
                    wids = [ctx['warehouse']]
                elif isinstance(ctx['warehouse'], basestring):
                    domain = [('name', 'ilike', ctx['warehouse'])]
                    if ctx.get('force_company', False):
                        domain += [('company_id', '=', ctx['force_company'])]
                    wids = warehouse_obj.search(cr, uid, domain, context=ctx)
                else:
                    wids = ctx['warehouse']
            else:
                wids = warehouse_obj.search(cr, uid, [], context=ctx)

            for w in warehouse_obj.browse(cr, uid, wids, context=ctx):
                location_ids.append(w.view_location_id.id)

        #_logger.info("Locations %s:%s" % (location_ids, ctx))
        locations = location_obj.browse(cr, uid, location_ids, context=ctx)
        for location in locations:
            ctx.update({'location': location.id})
            dql, dmil, domain_move_out_loc = self.with_context(ctx)._get_domain_locations()
            #_logger.info("Average consumation %s->%s" % (domain_move_out_loc, ctx))
            #self.env.cr, self.env.uid,
            moves_out = self.env['stock.move'].read_group(
                            domain_move_out + domain_move_out_loc, 
                            ['product_id', 'product_qty'], 
                            ['product_id'])
            moves_out = dict(map(
                lambda x: (x['product_id'][0], x['product_qty']), moves_out))
            product_ids = [k for k in moves_out.keys()]
            _logger.info("Compute %s:%s:%s" % (moves_out, product_ids, location.id))
            for product in self.browse(product_ids):
                begin_date = (
                    datetime.datetime.today() -
                    datetime.timedelta(days=product.calculation_range)
                    ).strftime('%Y-%m-%d')
                first_date = max(
                    begin_date,
                    self._min_date(product.id)
                    )
                nb_days = (
                    datetime.datetime.today() -
                    datetime.datetime.strptime(first_date, '%Y-%m-%d')
                    ).days
                for move in filter(lambda k: k == product.id, moves_out.keys()):
                    consumption_ids = consumption_obj.search(cr, uid, [('product_id', '=', product.id), ('location_id', '=', location.id)], context=self.env.context)
                    if len(consumption_ids):
                        for consumption in consumption_obj.browse(cr, uid, consumption_ids, context=self.env.context):
                            _logger.info("Teka %s" % consumption)
                            #consumption.product_id = product.id
                            #consumption.location_id = location.id
                            consumption.outgoing_qty = moves_out[move]
                            consumption.nb_days = nb_days
                    else:
                        vals = {
                                'product_id': product.id,
                                #'product_tmpl_id': product.product_tmpl_id.id,
                                #'company_id': ,
                                'location_id': location.id,
                                'outgoing_qty': moves_out[move],
                                'nb_days': nb_days,
                            }
                        consumption_obj.create(cr, uid, vals, context=self.env.context)

    @api.onchange('display_range', 'average_consumption')
    def _displayed_average_consumption(self):
        for product in self:
            product.displayed_average_consumption =\
                product.average_consumption * product.display_range
