#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Calibrate raw fits from telescope with 
#the corresponding darks and flats
#Input:list of fits files to calibrate
#Output:same names but in output directory
#config file parameters:

#Nacho Mas Ocutbre  2013
#Status: 

import fitsMaths


import commands,os, sys

from eUconfig import *


class calibrator:
	def do(self,fits,telescopeN=-1,calibrate=True,invert=True):
		if telescopeN==-1:
			print "CALIBRATOR:TELESCOPE NOT DEFINED"
			exit(1)
	 	cfg=dict(config.items('CALIBRATOR'))	
	 	flat_files=cfg['flat_file'].split(',')	
	 	dark_files=cfg['dark_file'].split(',')
		badpix_files=cfg['badpix_file'].split(',')
		os.chdir(cfg['tmp_dir'])

		if calibrate:
	 	    for i,f in enumerate(fits):
			arg=os.path.basename(f)
			dir_dest=os.path.dirname(f)
			filein=dir_dest+'/I'+arg
			print f,"rename to ->",filein
			os.rename(f,filein)	
			arg=os.path.basename(f)
		 	flat_file=flat_files[telescopeN]
		 	dark_file=dark_files[telescopeN]
			badpix_file=badpix_files[telescopeN]
			print "Calibrating :",arg,"\n"
			print f

			light=fitsMaths.fitMaths(filein)
			dark_sustracted=light.dark(dark_file)
			flated=dark_sustracted.flat(flat_file)
			flated.save(f)

		####INVERT THE FRAME TO FOLLOW LA SAGRA STANDARD
		if invert:
	 	   for i,f in enumerate(fits):
			pass

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	cali=calibrator()
	cali.do(fitsFiles)
