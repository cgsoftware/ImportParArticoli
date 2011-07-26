# -*- encoding: utf-8 -*-

import math

from osv import fields,osv
import tools
import ir
import pooler
import tools
import time
from tools.translate import _
import csv
import sys
import os
import re

class res_partner(osv.osv):
    _inherit='res.partner'
    _columns = {         
                'parimpproduct': fields.one2many('par.imp.product', 'supplier_id', 'supplier_id'),
                
                }
    
    def _import_product_func(self, cr, uid,lines,fornitore_id, context):
        inseriti = 0
        aggiornati = 0
        pool = pooler.get_pool(cr.dbname)
        product_obj = pool.get('product.product')     
        partner_obj = pool.get('res.partner')
        par_imp_product_obj = pool.get('par.imp.product')
        idPar = fornitore_id
        lista_idspar = par_imp_product_obj.search(cr,uid,[('supplier_id', '=',idPar)])
        lista_parametri = par_imp_product_obj.read(cr, uid, lista_idspar, ['column_name_product','column_number_file_import','eval_function'], context) 
        for riga in  lines:
            #import pdb;pdb.set_trace()
            #riga = riga.replace('"', '')
            #riga = riga.split(";")
            Articolo = dict() 
            for riga_par in lista_parametri:
                campo = riga_par['column_name_product']
                colonnacsv = int(riga_par['column_number_file_import'])-1
                if colonnacsv == -1:
                    #import pdb;pdb.set_trace()                    
                    # deve costruire il campo dalla funzione, i caratteri di costruzione
                    # sono separati dalla virgola, per o/ra somma soltanto le colonne interessate e /
                    # cli eventuali separatori inseriti 19/10/2010
                    funzione = riga_par['eval_function'].split(",")
                    calcolo =''
                    for car in funzione:
                        if type(eval(car)) == str:
                            calcolo=calcolo+car
                        else:
                            calcolo=calcolo+riga[int(car)-1]
                    Articolo[campo]= calcolo
                else:
                    Articolo[campo] = riga[colonnacsv] 
            # HA COSTRUITO IL DIZIONARIO CON L'ARTICOLO LO CERCA PER CODICE PER DECIDERE SE INSERIRE 
            # O MODIFICARE IL SOLO PREZZO PER ORA C&G 15/10/2010
            #import pdb;pdb.set_trace() 
            # CONTROLLO UNITA' DI MISURA
            if Articolo.has_key('uom_id'):            
                if Articolo['uom_id']:
                    argoment = [('name',"=",Articolo['uom_id'])]
                    item = pool.get('product.uom').search(cr,uid,argoment) 
                    if item:
                        Articolo['uom_id']=item[0]
                        Articolo['uom_po_id']=item[0]
                    else:
                        #import pdb;pdb.set_trace()
                        Articolo['uom_id']=1
                        # raise osv.except_osv(('Warning !'),('L unità di misura non può essere vuota !'))                        
                        Articolo['uom_po_id']=1                     
            # CONTROLLO Categoria Articolo
            if Articolo.has_key('categ_id'):
                if Articolo['categ_id']:
                    item = pool.get('product.category').search(cr,uid,[('name',"=",Articolo['categ_id'])]) 
                    if item:
                        Articolo['categ_id']=item[0]
                    else:
                        Articolo['categ_id']=1            
            # CONTROLLO Marchio Articolo
            if Articolo.has_key('marchio_ids'):                      
                if Articolo['marchio_ids']:
                    item = pool.get('marchio.marchio').search(cr,uid,[('name',"=",Articolo['marchio_ids'])]) 
                    if item:
                        Articolo['marchio_ids']=item[0]
                    else:
                        Articolo['marchio_ids']=0   
            #controlla i campi prezzo
            if Articolo.has_key('price'):
                Articolo['price'] = Articolo['price'].replace(',','.')     
            if Articolo.has_key('standard_price'):
                Articolo['standard_price'] = Articolo['standard_price'].replace(',','.')
                Articolo['list_price']=Articolo['standard_price']
            #import pdb;pdb.set_trace()
            if Articolo.has_key('ean13'): # CONTROLLA PRIMA CHE IL BAR CODE SIA VALIDO PER PROCEDERE
                if True: #check_ean(Articolo['ean13'])
                    ok = True
                else:
                    ok = False
            else:
                ok = True
            if ok:
                RecArticolo = product_obj.search(cr,uid,[('default_code', '=',Articolo['default_code'])])
                if RecArticolo:
                    # ARTICOLO ESISTENTE
                    # import pdb;pdb.set_trace()
                    TemplateId=pool.get('product.product').read(cr, uid, RecArticolo, ['product_tmpl_id'])
                    ok = product_obj.write(cr,uid,RecArticolo,Articolo)
                    ok = pool.get('product.template').write(cr,uid,[TemplateId[0]['id']],Articolo)
                    aggiornati +=1
                else:
                    #DEVE PREPARARE LA INSERT  con eventuali altri controlli aggiuntivi  
                    ArticoloId = product_obj.create(cr,uid,Articolo)
                    #import pdb;pdb.set_trace()
                    # INSERISCE I DATI FORNITORE
                    Fornitore = dict()
                    item = pool.get('product.product').search(cr,uid,[('id',"=",ArticoloId)])
                    TemplateId=pool.get('product.product').read(cr, uid, item, ['product_tmpl_id'])
                    inseriti +=1
                    for riga in TemplateId:
                        Template = riga['product_tmpl_id']
                        Fornitore = {
                                    'product_id':Template[0],
                                    'name':idPar,
                                    'qty':1,
                                    'min_qty':1,
                                    'delay':1,
                                    'product_uom': Articolo['uom_id']
                                    }
                        FornitoreArtId = pool.get('product.supplierinfo').create(cr,uid,Fornitore)
                    #import pdb;pdb.set_trace()            
        return [inseriti,aggiornati]

                
    def run_auto_import(self, cr, uid, automatic=False, use_new_cursor=False, context=None):
      pool = pooler.get_pool(cr.dbname)  
      #import pdb;pdb.set_trace()
      testo_log = """Inizio procedura di aggiornamento/inserimento articoli """+time.ctime()+'\n'
      percorso='/home/openerp/filecsv'
      partner_obj = pool.get('res.partner')
      if use_new_cursor:
        cr = pooler.get_db(use_new_cursor).cursor()
      elenco_csv = os.listdir(percorso)
      for filecsv in elenco_csv:
        codfor=filecsv.split(".")
        testo_log = testo_log + " analizzo file "+codfor[0]+".csv \n"
        fornitore_ids = partner_obj.search(cr,uid,[('ref', '=',codfor[0])])
        if fornitore_ids:
          fornitore_id = fornitore_ids[0]
          lines = csv.reader(open(percorso+'/'+filecsv,'rb'),delimiter=";")
          #import pdb;pdb.set_trace() 
          res = self._import_product_func(cr, uid, lines, fornitore_id, context)
          testo_log = testo_log + " Inseriti "+str(res[0])+" Aggiornati "+str(res[1]) +" Articoli \n"
        else:
          testo_log = testo_log + " fornitore "+codfor[0]+" non trovato  \n"
        os.remove(percorso+'/'+filecsv)
      testo_log = testo_log + " Operazione Teminata  alle "+time.ctime()+"\n"
      #invia e-mail
      type_ = 'plain'
      tools.email_send('info@ciciriello.it',
                       ['mino@ciciriello.it'],
                       'Import Automatico Articoli',
                       testo_log,
                       subtype=type_,
                       )

        
      return
    
 

res_partner()

##def _sel_func_old(self, cr, uid, context={}):
##	obj = self.pool.get('ir.model.fields')
####	search(cr,uid,[('model','=','product.product')])
##	ids = obj.search(cr,uid,[('model','=','product.product')])
####	res = obj.read(cr, uid, ids, [’name’, ’field_description’], context)
##	res = obj.read(cr, uid, ids, ['id', 'name'], context)
##	res = [(r[’id’], r[’name’]) for r in res]
##	return res

def _elenco_campi(self, cr, uid, context={}):
    obj = self.pool.get('ir.model.fields')
    ids = obj.search(cr, uid, [('model', '=', 'product.product')])
    res = obj.read(cr, uid, ids, ['name','name'], context)
    obj2 = self.pool.get('ir.model.fields')
    ids2 = obj2.search(cr, uid, [('model', '=', 'product.template')])
    res2 = obj2.read(cr, uid, ids2, ['name','name'], context)    
    return [(r['name'], r['name']) for r in res] + [(r2['name'], r2['name']) for r2 in res2]


class par_imp_product(osv.osv):
    _description ='Parameter for import Product'
    _name = 'par.imp.product'
    _order = 'id'
    

    _columns = {
        'supplier_id': fields.many2one('res.partner', 'Partner', ondelete='set null', select=True, help="Parameter for Import Export Catalog"),
        'column_name_product': fields.selection( _elenco_campi,'Campo Articolo',size=150),        
        'column_number_file_import': fields.char('Numero Colonna', size=10),
        'eval_function': fields.char('Funzione di Costruzione', size=128),
    }
    

    
    
 
 
par_imp_product()
