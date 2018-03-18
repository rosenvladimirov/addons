# -*- coding: utf-8 -*-
# © 2015 Roberto Lizana (Trey)
# © 2016 Pedro M. Baeza
# © 2017 Rosen Vladimirov
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    cr.execute("""
    INSERT INTO res_partner_id_number
    (partner_id, name, category_id, status, active)
    SELECT id, company_registry, 1, 'open', TRUE
    FROM res_partner
    WHERE company_registry IS NOT NULL""")
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("""
    INSERT INTO res_partner_id_number
    (partner_id, name, category_id, status, active)
    SELECT id, vat, 2, 'open', TRUE
    FROM res_partner
    WHERE vat IS NOT NULL""")
    env = api.Environment(cr, SUPERUSER_ID, {})
