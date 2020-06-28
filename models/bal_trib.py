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


class bal_trib_reportes_chile(models.TransientModel):
    _inherit = 'wizard.reportes.chile'  

    @api.multi
    def _balance_tributario(self,wizard=False):
        if wizard:  
            wiz = self.search([('id','=',wizard)])
        else:
            wiz = self        
        company = int(wiz.company_id.id)        
        fecha_inicio = datetime.strptime(wiz.fecha_inicio, '%Y-%m-%d').date()
        fecha_term = datetime.strptime(wiz.fecha_term, '%Y-%m-%d').date()
        self.env.cr.execute("""
            SELECT aa.code,aa.name,aat.report_type,sum(aml.debit),sum(aml.credit)
            FROM account_move_line aml,account_account aa,account_account_type aat, account_move am
            WHERE   aml.account_id=aa.id and aa.user_type_id = aat.id 
                    and aml.move_id=am.id and am.state='posted'
                    and aml.company_id = %i 
                    and (aml.date >= to_date('%s', 'YYYY-MM-DD') and aml.date <= to_date('%s', 'YYYY-MM-DD'))
            GROUP BY aa.code,aa.name,aat.report_type order by aa.code
            """ %(company,fecha_inicio,fecha_term))          
        dic = OrderedDict([            
            ('Codigo',''),
            ('Cuenta',''),
            ('Tipo',''),            
            ('Debe',0.0),
            ('Haber',0.0),                         
            ])
        lista = []        
        for record in self.env.cr.fetchall():            
            dicti = OrderedDict()
            dicti.update(dic)
            dicti['Codigo']=record[0]
            dicti['Cuenta']=record[1]
            dicti['Tipo']=record[2]
            dicti['Debe']=float(record[3])
            dicti['Haber']=float(record[4])
            lista.append(dicti) 
        tabla = pd.DataFrame(lista)
        #_logger.error(tabla)
        if tabla.empty:
            raise exceptions.Warning('No hay datos para mostrar')
        #tabla = wiz._libro_diario()        
        #tabla = pd.DataFrame(tabla.groupby(['Codigo','Tipo','Cuenta'], as_index=False).sum())        
        tabla['Deudor']=tabla[(tabla['Debe']-tabla['Haber']>=0)]['Debe']-tabla[(tabla['Debe']-tabla['Haber']>=0)]['Haber']
        tabla['Acreedor']=tabla[(tabla['Debe']-tabla['Haber']<0)]['Haber']-tabla[(tabla['Debe']-tabla['Haber']<0)]['Debe']                
        tabla['Activo']=tabla[(tabla['Tipo'].isin(['asset','liability']))]['Deudor']
        tabla['Pasivo']=tabla[(tabla['Tipo'].isin(['asset','liability']))]['Acreedor']
        tabla['Perdida']=tabla[(tabla['Deudor']>0)&(tabla['Tipo'].isin(['income','expense']))]['Deudor']
        tabla['Ganancia']=tabla[(tabla['Acreedor']>0)&(tabla['Tipo'].isin(['income','expense']))]['Acreedor']
        tabla.fillna(0, inplace=True)                
        return tabla.drop(['Tipo'], axis=1)
        
class account_account_type(models.Model):
    _inherit = 'account.account.type'

    report_type = fields.Selection(string='Categoria de Cuenta', store=True,
            selection= [('income', 'Ingresos'),
                        ('expense','Egresos'),
                        ('asset','Activos'),
                        ('liability','Pasivos')])
        