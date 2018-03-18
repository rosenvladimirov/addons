# -*- coding: utf-8 -*-
# Copyright (C) 2016-Today GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp import api, models, fields, exceptions, _
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _compute_pricelist_version(self):
        for partner in self:
            version = False
            for v in partner.property_product_pricelist.version_id:
                if (v.pricelist_visable) and ((v.date_start is False) or (v.date_start <= date)) and ((v.date_end is False) or (v.date_end >= date)):
                    version = v
                    break
            if not version:
                partner.property_product_pricelist_version = ''
            else:
                partner.property_product_pricelist_version = version.name

    @api.multi
    def _compute_show_pricelist_version(self):
        for partner in self:
            version = False
            for v in partner.property_product_pricelist.version_id:
                if (v.pricelist_visable) and ((v.date_start is False) or (v.date_start <= date)) and ((v.date_end is False) or (v.date_end >= date)):
                    version = v
                    break
            if not version:
                partner.pricelist_visable = False
            else:
                partner.pricelist_visable = version.pricelist_visable

    property_product_pricelist_version = fields.Char(
        string='Version of pricelist', store=False,
        compute='_compute_pricelist_version', multi='pricelist_version', help='Current version of The pricelist')
    pricelist_visable = fields.Char(
        string='Version of pricelist is visabled', store=False,
        compute='_compute_show_pricelist_version', multi='pricelist_version', help='Show current version of The pricelist')
