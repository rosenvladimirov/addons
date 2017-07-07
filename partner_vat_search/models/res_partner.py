# -*- coding: utf-8 -*-
# © 2012-2014 Guewen Baconnier (Camptocamp SA)
# © 2015 Roberto Lizana (Trey)
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
import operator

import logging
_logger = logging.getLogger(__name__)

domain_old_part = []

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def search(self, domain, *args, **kwargs):
        global domain_old_part
        if filter(lambda x: x[0] == 'vat', domain):
            #_logger.info("Start Filter %s:%s" % (domain, domain_old_supp))
            counter = len(filter(lambda x: x[0] == 'vat', domain))
            if counter > 1:
                j = 0
                for i,x in enumerate(domain):
                    if x[0] == 'vat' and j < counter-1:
                        #_logger.info("domain %s:%s:%s" % (x[0], i, j))
                        domain[i] = domain_old_part[j]
                        j += 1
            else:
                domain_old_part = []
            supp_code_operator = filter(lambda x: x[0] == 'vat', domain)[0][1]
            supp_code_value = filter(lambda x: x[0] == 'vat', domain)[0][2]
            suppinfo = self.env['res_partner'].search(
                               [('product_code', supp_code_operator, supp_code_value)])
            domain = filter(lambda x: x[0] != 'seller_ids.product_code', domain)
            _logger.info("Filter %s" % domain)
            domain_old_supp.append(('id', 'in', [suppinfo.product_tmpl_id.product_variant_ids]))
            domain += [domain_old_supp[-1]]
            _logger.info("After Filter %s:%s" % (domain, domain_old_supp))
        return super(ProductProduct, self).search(domain, *args, **kwargs)
