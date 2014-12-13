#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETFSuit
#Category: Posprocessing

import commands,os, sys,glob

from PIL import Image,ImageDraw,ImageFont
import f2n
import copy


class cropperClass:


	def loadWCSfromFits(self,fits):
		self.wcsFits=fits


	def loadImageFromFits(self,fits):
		self.fitsToCrop = f2n.fromfits(fits)


	def cropRADEC(self,ra,dec,deltaRA,deltaDEC,fichero):
		print "Generating crop from:",fits, "RA,DEC,deltas coords:",ra,dec,deltaRA,deltaDEC
		coords0=(self.wcs2pix(self.wcsFits,RA-deltaRA,DEC-deltaDEC))
		coords1=(self.wcs2pix(self.wcsFits,RA+deltaRA,DEC+deltaDEC))
		if coords0==(0,0) and coords1==(0,0):
			print "RA/DEC to x,y FAIL ",fichero," not create"
			return False
		(x0,y0)=map(lambda x:int(x),coords0)
		(x1,y1)=map(lambda x:int(x),coords0)
		return self.cropXY(self,x0,x1,y0,y1,fichero)


	def cropXY(self,x0,x1,y0,y1,fichero,negative=True):
	   try:
		print "Generating crop from:",self.fitsToCrop, "x,y coords:",x0,x1,y0,y1
		myimage = copy.deepcopy(self.fitsToCrop)
		myimage.crop(x0,x1,y0,y1)
		myimage.setzscale(z1="auto",z2="flat",samplesizelimit=10000,nsig=3)
		#myimage.setzscale(z1="auto",z2="auto",samplesizelimit=10000,nsig=3)
		#myimage.setzscale(-1000,5000)
		# z2 = "ex" means extrema -> maximum in this case.
		if negative:
			myimage.makepilimage("log", negative = True)
		else:
			myimage.makepilimage("lin")
		# We can choose to make a negative image.
		myimage.tonet(fichero)

           except:
		print "FAIL to crop"
		return False

	   return True	


	def test(self):
		print "Generating PNG from:",fits
		myimage = copy.deepcopy(self.fitsToCrop)
		myimage.crop(70, 270, 60, 260)
		myimage.setzscale("auto")
		# z2 = "ex" means extrema -> maximum in this case.
		myimage.makepilimage("log", negative = True)
		# We can choose to make a negative image.
		myimage.tonet("test.png")

def writeGif(AnimateGif, imgs, duration=0.4):
	use_convert=True
	if use_convert:
		#animategif library do not work properly
		#use ImageMagick instead
		cmd="convert -delay "+str(duration*100)+" -loop 0 "
		for im in imgs:
			cmd=cmd+im+" "
		cmd=cmd+AnimateGif
		res=commands.getoutput(cmd)
		print res
	else:
		from images2gif import writeGif
		imgsI = [Image.open(fn) for fn in imgs]
		writeGif(AnimateGif, imgsI, duration)

if __name__ == '__main__':
	fits=sys.argv[1:][0]
	cropper=cropperClass()
	cropper.loadImageFromFits(fits)
	cropper.loadWCSfromFits(fits)
	cropper.test()	





