#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing

import commands,os, sys,glob
import simplejson
import eUdss
import eUcropper
import eUfitCrop

from PIL import Image,ImageDraw,ImageFont
import cPickle as pickle
import numpy as np
import urllib

from eUconfig import *

cfg=dict(config.items("SUPERNOVA"))

class SN_Hunter(eUcropper.cropperClass,helper):

        def do(self):
	   for i,fits in enumerate(self.solvefits):	
		ra  = self.centers[i][0]
		dec = self.centers[i][1]

		path=cfg['dir_image_base']+'/'+self.getToday()+'/'+cfg['galaxy_image']
		if not os.path.exists( path):
	    		os.makedirs(path)

		self.cropGalaxies(fits,ra,dec)

        def getGalaxies(self,fits,ra,dec):
           	#url="http://localhost:9000/hyperleda"
		url=cfg['galaxy_server']
		d = {}
		d['ra']  = ra
		d['dec'] = dec
		d['r'] = 1.5
		d['format']="pickle"
		url_values = urllib.urlencode(d)
		full_url = url + '?' + url_values
		handle= urllib.urlopen(full_url)
		galaxiesCat = pickle.load(handle)
		handle.close()
		return galaxiesCat

	def cropGalaxies(self,fits,ra,dec):
		self.loadImageFromFits(fits)
		self.loadWCSfromFits(fits)
		for galaxy in self.getGalaxies(fits,ra,dec):
			if len(galaxy['Names'])!=0:
				name=galaxy['Names'].split(' ')[0]
			else:
				name='PGC'+galaxy['PGC']
			ra=float(galaxy['RA'])
			dec=float(galaxy['DEC'])
			minsize=60.
			r=max(float(galaxy['D'])/3600.,minsize/3600.)
			print name,ra,dec,r

		        if eUfitCrop.fitCropy(fits, ra, dec, r, r, units='wcs', outfile=path+'/'+name+'.fit'):
				self.cropRADEC(ra,dec,r,r,path+'/'+name+'.png',negative=False)
				self.getDSS(ra,dec,2*r*60,path+'/'+name+'.dss')
				self.sex(path+'/'+name+'.fit',name+'.cat')
				self.sex(path+'/'+name+'.dss.fit',name+'.dss.cat')
			else:
				continue

	def sex(self,fit,name):
		sexStr="sex "+fit+" -c "+cfg["sexcfg"]+" -CATALOG_NAME "+name+" -FILTER Y -FILTER_NAME "+cfg["sexfilter"]+ \
		" -CATALOG_TYPE FITS_1.0  " +" -PARAMETERS_NAME "+cfg["sexparam"]
		print "EXECUTING:",sexStr
		res=commands.getoutput(sexStr)
		print res
		hdulist=pyfits.open(name)
		return hdulist

	def getDSS(self,ra,dec,r,name):
		dss=eUdss.DSS()
		dss.pngGet(ra,dec,r,name)

	def writeJson(self):
		#NOT FINISHED!!	
		path=cfg['dir_image_base']+'/'+self.getToday()+'/'+cfg['galaxy_image']
		filename=path+"/supernova.json"
		movers=self.data
		moversIDs=set(movers['ID'])
		json_dict={'FRAME':self.frame,'SLOWMOVERS':[]}
		json_dict_reduce={}
	  	for moverID in moversIDs:
			print "JSON mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			m=mover[0]
			if not math.isnan(round(m['DIS_MPC'],0)):
				oc=round(m['DIS_MPC'],0)
			else:
				oc="-"
			mpcobs=self.writeMPC('/dev/null',ID=moverID)
			#r="%4.3e" % m['CORRELATION']
			r="%4.3e" % m['RMS']
			entry= {'ID':moverID,'MAG':round(m['MEAN_MAG'],1),'SPEED':round(m['MEANspeed'],1),'PA':round(m['PA'],1), \
				'KNOW':bool(m['KNOW']),'OC':oc,'R':r,'MPCOBS':mpcobs}
			entryReduce= {moverID:{'MAG':round(m['MEAN_MAG'],1),'SPD':round(m['MEANspeed'],1),'PA':round(m['PA'],1),'KNW':bool(m['KNOW']),'OC':oc,'R':r}}
			#print moverID,entry
			json_dict['SLOWMOVERS'].append(entry)
			json_dict_reduce.update(entryReduce)
		x = simplejson.dumps(json_dict)
	        fi=open(filename,"w")
		fi.write(x)
		fi.close()	
		print json_dict_reduce
		return 	json_dict_reduce


if __name__ == '__main__':
	fits=sys.argv[1:][0]
	fitsFiles=sys.argv[1:]
	sn=SN_Hunter(fitsFiles)
	sn.do()






