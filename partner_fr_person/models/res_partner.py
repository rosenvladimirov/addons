# -*- coding: utf-8 -*-
#    Copyright (c) 2014 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2015 Antiun Ingeniería S.L. (http://www.antiun.com)
#                       Antonio Espinosa <antonioea@antiun.com>
# © 2015 Antiun Ingeniería S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fr_person = fields.Char(
        string="FR Person", required=True,
        help="Representer ot The Company. For example, Company manager.")

class ResPartnerJobPosition(models.Model):
    _inherit = = "res.partner.job_position"

    def _get_fieldname(self):
        return [('fr_person', 'Representer of The company'), ('wh_person', 'Wharehause manager'),]

    fieldname = fields.Selection(
        _get_fieldname,
        'Choice field name to fill', default='fr_person')
