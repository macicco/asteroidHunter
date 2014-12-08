#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import pyfits
import math
import commands,os, sys,shutil
from eUconfig import *

class astrometryQA:

	def do(self,filename):
		extensions=["ORIGINAL","CLEAN","ASTROMETRY_NODISTORSION","ASTROMETRY_SIP2PV","SCAMP"]
		self.files=map(lambda x:x+"_"+filename,extensions)
		print self.files
		for f in self.files:
			res=commands.getoutput("rm "+f)
			#print res
		 	shutil.copy(filename,f)
		self.cleanHeader("CLEAN_"+filename)
		self.cleanHeader("ASTROMETRY_NODISTORSION_"+filename)
		self.cleanHeader("ASTROMETRY_SIP2PV_"+filename)
		self.cleanHeader("SCAMP_"+filename)
		
		self.astrometrySolver("ASTROMETRY_NODISTORSION_"+filename," --tweak-order 1")
		self.astrometrySolver("SCAMP_"+filename,"  --tweak-order 1 --scamp-ref ref.scamp --scamp image.scamp --scamp-config scamp.conf")
		self.astrometrySolver("ASTROMETRY_SIP2PV_"+filename," --tweak-order 4")

		#SIP2PV
		f="ASTROMETRY_SIP2PV_"+filename
		ff="_ASTROMETRY_SIP2PV_"+filename
		res=commands.getoutput("rm "+ff)
		print res
		res=commands.getoutput("sip2pv -i "+f+" -o "+ff)
		print res
		res=commands.getoutput("rm "+f)
		print res
		res=commands.getoutput("mv "+ff+" "+f)
		print res
		res=commands.getoutput("sip2pv -i "+f+" -o "+ff)
		print res
		#SCAMP
		res=commands.getoutput("scamp -c scamp.conf image.scamp")
		print res

	
		for f in self.files:
		 	self.sex(f)

	def updateheader(self,filename,newheader):
		hdulist = pyfits.open(arg,mode='update')
		#hdulist.info()
		header = hdulist[0].header
		if isinstance(value, str):
			value=value.strip()
			print value
		header[name]=(value,comment)
		#print header
		hdulist.close()


	def cleanHeader(self,arg):
		cfg=dict(config.items("CLEANHEADER"))
		KEEPheader=cfg["keepheader"]
		print ""	
       		print "CLEANING HEADER FITS:",arg
		hdulist = pyfits.open(arg,mode='update')
		header=hdulist[0].header
		for key in header.keys():
			if not key in KEEPheader:
				print "Deleting ",key
				del header[key]

		hdulist.close()
		return 

	def astrometrySolver(self,filename,xtraparams):
		parameters="-p --overwrite -z 2 -y -g -l 60 "
		cmd='solve-field  '+parameters+' '+xtraparams+' '+filename
		print cmd
		res=commands.getoutput(cmd)
		print res
		res=commands.getoutput("rm "+filename)
		print res
		res=commands.getoutput("mv "+filename.replace("fit","new")+" "+filename)
		print res
		for ext in (".axy",".wcs",".corr",".solved",".match",".rdls","-indx.xyls"):
			res=commands.getoutput("rm "+filename.replace(".fit","")+ext)
			print res


		


	def sex(self,filename):
		print "Sextracting:",filename
		cfg=dict(config.items("SEXASTEROIDS"))
		hdulist = pyfits.open(filename)
		hdr = hdulist[0].header
		try:
		        date=hdr['DATE-OBS']
		except:
			try:
				date=hdr['DATE']
			except:
				print "FITS NOT CONTAING DATE/DATE-OBS KEY"
				exit(0)

		try:
		        ZP=hdr['ZMAG']
		except:
			try:
				ZP=hdr['ZEROPOINT']
			except:
				ZP=float(cfg['default_zeropoint'])
				print "FITS NOT CONTAING ZMAG/ZEROPOINT KEY"
				print "Using defaults:"	+str(ZP)
	
		try:
		        GAIN=hdr['EGAIN']
		except:
			try:
				GAIN=hdr['GAIN']
			except:
				print "FITS NOT CONTAING GAIN/EGAIN KEY"
				GAIN=0
		try:
			exposure=hdr['EXPTIME']
		except:
			print "FITS NOT CONTAING EXPOSURE KEY"
			exit(0)

		ZP=ZP+2.5*math.log10(exposure)
		print "SETTING ZP",2.5*math.log10(exposure)


		sexStr="sex "+filename+" -c "+cfg["sexcfg"]+" -CATALOG_NAME "+filename.replace("fit","cat")+" -FILTER Y -FILTER_NAME "+cfg["sexfilter"]+ \
		" -CATALOG_TYPE FITS_1.0  " +" -PARAMETERS_NAME "+cfg["sexparam"]+" -MAG_ZEROPOINT "+str(ZP)+ \
		" -DETECT_THRESH "+cfg["sigma"] + " -GAIN "+str(GAIN) 

		print "EXECUTING:",sexStr
		res=commands.getoutput(sexStr)
		print res




if __name__ == '__main__':
	fits=sys.argv[1:][0]
	QA=astrometryQA()
	QA.do(fits)
