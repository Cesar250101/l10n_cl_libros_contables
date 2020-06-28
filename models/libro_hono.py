from odoo import models, fields, api, exceptions
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import xlsxwriter
from io import StringIO
import base64
import pandas as pd
import numpy as np
import logging

_logger = logging.getLogger(__name__)


class libro_hono_reportes_chile(models.TransientModel):
    _inherit = 'wizard.reportes.chile'    

    @api.multi
    def _libro_honorarios(self,wizard=False):
        if wizard:  
            wiz = self.search([('id','=',wizard)])
        else:
            wiz = self                
        search_domain = wiz._get_domain()
        search_domain += [
            ('state','in',['open','paid']),            
            ('type','in',['in_invoice']),
            ('sii_code','in',['70','71'])
            ]  
        docs = wiz.env['account.invoice'].search(search_domain, order='reference asc')
        if not docs:
            raise exceptions.Warning('No hay datos para mostrar con los filtros actuales')        
        dic = OrderedDict([
            ('Tipo',''),
            ('Numero',''),
            ('Fecha',''),
            ('RUT',''),
            ('Nombre',''),
            ('Bruto',''),
            ('Retencion',''),
            ('A pagar',''),
            ])
        lista = []
        for i in docs:
            dicti = OrderedDict()
            dicti.update(dic)
            dicti['Tipo']='BH'
            dicti['Numero']=i.reference
            dicti['Fecha']=i.date_invoice
            dicti['RUT']=i.partner_id.document_number
            dicti['Nombre']=i.partner_id.name
            dicti['Bruto']=i.amount_untaxed
            dicti['Retencion']=abs(i.amount_retencion)
            dicti['A pagar']=i.amount_total 
            lista.append(dicti)    
        tabla = pd.DataFrame(lista)  
        return tabla 