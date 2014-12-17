#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing

import commands,os, sys,glob
import simplejson
import eUdss
import eUcropper
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
			path=cfg['dir_image_base']+'/'+self.getToday()+'/'+cfg['galaxy_image']
			if not os.path.exists( path):
	    				os.makedirs(path)
			if not self.cropRADEC(ra,dec,r,r,path+'/'+name+'.png',negative=False):
				continue
			self.getDSS(ra,dec,2*r*60,path+'/'+name+'.dss')

	def getDSS(self,ra,dec,r,name):
		dss=eUdss.DSS()
		dss.pngGet(ra,dec,r,name)

if __name__ == '__main__':
	fits=sys.argv[1:][0]
	fitsFiles=sys.argv[1:]
	sn=SN_Hunter(fitsFiles)
	sn.do()






