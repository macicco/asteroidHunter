#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#EETF Suite
#Category: Posprocessing
#Prepare html an images to show the result
#Input:'Gcandidates_'{framename}.cat
#Output:same names but with 'Gmover_' file prefix
#config file parameters:
#
#	Section: [ACROPPIES]
#		html_base_dir
#		croppy_size
#		animation_margin
#
#Nacho Mas Junio 2013
#Status: work. Further housekeeping needed

import pyfits
from pylab import *
import commands,os, sys
import shutil
import csv
import re
import numpy as np
import eUcatalog
from pyraf import iraf
from pyraf.gki import printPlot
from images2gif import writeGif
from PIL import Image,ImageDraw
import glob
from pylab import *

from eUconfig import *

cfg=dict(config.items("ACROPPIES"))


def Debug(string):
	debug=cfg["debug"]
	if debug in ['True','true','yes','y']:
		print string

class cropClass(eUcatalog.moverCat,helper):
	tam=int(cfg["croppy_size"])
	margen=int(cfg["animation_margin"])

	def do(self):
		self.htmldir=cfg["html_base_dir"]+"/"+self.getToday()+"/"+self.frame
		self.FitsDir=self.htmldir+"/FitsDir"
		self.ImagesDir=self.htmldir+"/images"
		self.ContourDir=self.htmldir+"/contour"
		self.AnimationDir=self.htmldir+"/animations"
		self.CroppiesDir=self.htmldir+"/croppies"
		self.CorrelationDir=self.htmldir+"/correlation"
		self.MapsDir=self.htmldir+"/MapsDir"

		if not os.path.exists(self.htmldir):
			    os.makedirs(self.htmldir)
		self.basicFitData()
		res=commands.getoutput("cp "+configpath+"/nodata.gif "+self.htmldir+"/nodata.gif")
		res=commands.getoutput("cp "+configpath+"/eetf.css "+self.htmldir+"/.")
		self.loadFIT(self.Amovers)
		if 1:
			self.images()
			self.contour()
			self.croppies()
			self.animation()
			self.correlations()		
			#self.maps()
		self.moverMainFlt=0
		print self.moverMainFlt
		self.html()

	def cropper(self,fits,(x0,y0),(x1,y1),fitsout):
		deltaX=x1-x0
		deltaY=y1-y0
		print "CROPPER ARG:",x0,y0,x1,y1,deltaX,deltaY

		iraf.imexpr.expr="I*0.0+J*0.0"
		iraf.imexpr.output=fitsout
		iraf.imexpr.dims=str(deltaX)+","+str(deltaY) 
		iraf.imexpr()

		xx0=1
		yy0=1
		xx1=deltaX
		yy1=deltaY
	
		if x0<=0:
			xx0=-x0+1
			x0=1
		if y0<=0:
			yy0=-y0+1
			y0=1

		if x1>self.frameWidth:
			xx1=deltaX-(x1-self.frameWidth)
			x1=self.frameWidth
		if y1> self.frameHeight:
			yy1=deltaY-(y1-self.frameHeight)
			y1=self.frameHeight
		print "CROPPER SRC:",x0,y0,x1,y1
		print "CROPPER DST:",xx0,yy0,xx1,yy1
		if x1<=0 or y1<=0 or x0>= self.frameWidth or y0>=self.frameHeight:
			print "Out of limits"
			return False
		else:
			iraf.imcopy.input=fits+"["+str(x0)+":"+str(x1)+","+str(y0)+":"+str(y1)+"]"
			iraf.imcopy.output=fitsout+"["+str(xx0)+":"+str(xx1)+","+str(yy0)+":"+str(yy1)+"]"
			iraf.imcopy()
			return True


	def animation(self):
		AnimationDir=self.AnimationDir
		FitsDir=self.FitsDir
		if not os.path.exists(FitsDir):
			    os.makedirs(FitsDir)
		res=commands.getoutput("rm "+FitsDir+"/anima*" )
		#margen=10
		margen=self.margen
		movers=self.data
		moversIDs=set(movers['ID'])
		for moverID in moversIDs:
			print "Animation mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			RAmax=max(mover['ALPHA_J2000'])
			DECmax=max(mover['DELTA_J2000'])
			RAmin=min(mover['ALPHA_J2000'])
			DECmin=min(mover['DELTA_J2000'])
			maxCoord=("%s %s" % (RAmax,DECmax),"%s %s" % (RAmin,DECmin))
			RAs=mover['ALPHA_J2000']
			DECs=mover['DELTA_J2000']

			for i,id in enumerate(mover['frame']):
				print "Processing frame:",id
				#SrcFrame="S"+frame+"-%02u.fit" % int(id)
				SrcFrame=self.solvefits[int(id)-1]

				RA=RAs[i]
				DEC=DECs[i]
				
				(x0,y0)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RAmax,DECmax))))
				x0=x0-margen
				y0=y0+margen
				(x1,y1)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RAmin,DECmin))))
				x1=x1+margen
				y1=y1-margen
				(x,y)=map(lambda x:int(x),(self.wcs2pix(SrcFrame,(RA,DEC))))				
				x=x-x0
				y=y-y1

				deltaX=abs(x1-x0)/2
				deltaY=abs(y1-y0)/2

				print x,y

				ymean=(y0+y1)/2
				xmean=(x0+x1)/2
				print "ANI:",x,y,x0,y0,x1,y1,deltaX,deltaY
				tam=max(deltaX,deltaY)
				DstFrame=FitsDir+"/animation%s-%02u.fit" % (moverID,int(id))
				if os.path.isfile(DstFrame):
					os.remove(DstFrame)

				if not os.path.exists(AnimationDir):
			 		os.makedirs(AnimationDir)

				if not self.cropper(SrcFrame,(xmean-deltaX,ymean-deltaY),(xmean+deltaX,ymean+deltaY),DstFrame):
					continue
				

				AnimationGif="animation%s-%02u.gif" % (moverID,int(id))
				AnimationFrame=FitsDir+"/animation%s-%02u.fit" % (moverID,int(id))
				res=commands.getoutput("rm "+AnimationDir+"/"+AnimationGif)
				res=commands.getoutput("rm "+AnimationDir+"/"+AnimationGif+'.png')
			
				iraf.export.images=AnimationFrame
				iraf.export.format="gif"
				iraf.export.binfiles=AnimationDir+"/"+AnimationGif
				iraf.export.outbands="zscale(i1)"
				iraf.export(_save=0,mode='h')	
				im = Image.open(AnimationDir+"/"+AnimationGif).convert('RGB')
				draw = ImageDraw.Draw(im)
				draw.line(((x-5,y),(x+5,y)),width=1,fill='#ff0000')
				draw.line(((x,y-5),(x,y+5)),width=1,fill='#ff0000')
				del draw 
				im.save(AnimationDir+"/K"+AnimationGif+".png","PNG")
				
				img=Image.open(AnimationDir+"/"+AnimationGif)
				factor=1.
				maxAnimationSize=float(cfg["max_animation_size"])
				if deltaX>maxAnimationSize: 
					factor=(maxAnimationSize/deltaX)
				if deltaY>maxAnimationSize:
					factor=(maxAnimationSize/deltaY)
				print factor,deltaX,deltaY
				img1=img.resize((int(deltaX*factor),int(deltaY*factor)),Image.ANTIALIAS)
				#img1.show()
				img1.save(AnimationDir+"/"+AnimationGif)


			file_names = sorted((fn for fn in os.listdir(AnimationDir) if fn.startswith('animation%s-' %moverID)))
			imgs = [Image.open(AnimationDir+"/"+fn) for fn in file_names]
			if len(file_names)>0:
				print file_names
				#AnimateGif=AnimationDir+"/animate-%02u.gif" % moverID
				AnimateGif=AnimationDir+"/animate-%s.gif" % moverID
				writeGif(AnimateGif, imgs, duration=0.4)	


				



	def croppies(self):
		CroppiesDir=self.CroppiesDir
		if not os.path.exists(CroppiesDir):
		    os.makedirs(CroppiesDir)
		FitsDir=self.FitsDir
		if not os.path.exists(FitsDir):
		    os.makedirs(FitsDir)
		res=commands.getoutput("rm "+FitsDir+"/cropp*" )
		tam=self.tam
		movers=self.data
		moversIDs=set(movers['ID'])
		print moversIDs
		for moverID in moversIDs:
			#res=commands.getoutput("rm croppy"+str(moverID)+"*.fits" )
			print "Croping mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			for id in mover['frame']:
				print "Processing frame:",id
				#SrcFrame=frame+"-%02u.fit" % int(id)
				SrcFrame=self.solvefits[int(id)-1]
				moverFlt=(mover['frame']==id)
				mov=mover[moverFlt]
				print mov
				coord=[]
				coord.append("%s %s" % (mov['X_IMAGE'][0],mov['Y_IMAGE'][0]))
				print coord
				for idd in mover['frame']:
					print "Processing subframe:",moverID,"-",id,"-",idd
					#DstFrame=frame+"-%02u.fit" % int(idd)
					DstFrame=self.solvefits[int(idd)-1]
					iraf.skyctran.input="STDIN"
					iraf.skyctran.output="STDOUT"
					iraf.skyctran.insystem=SrcFrame+" logical"		
					iraf.skyctran.outsystem=DstFrame+" logical"
					s=iraf.skyctran(Stdin=coord,Stdout=1)
					print "Old coord:",coord
					print "New coord",s[10]
					newcoord=s[10].split()
					x1=int(float(newcoord[2]))
					y1=int(float(newcoord[3]))

					CropFrame=FitsDir+"/croppy%s-%02u-%02u.fit" % (moverID,int(id),int(idd))
					if os.path.isfile(CropFrame):
						os.remove(CropFrame)
					self.cropper(SrcFrame,(x1-tam,y1-tam),(x1+tam,y1+tam),CropFrame)

			res=commands.getoutput("rm "+CroppiesDir+"/croppies"+str(moverID)+".gif" )

			if 1:	
				iraf.files(FitsDir+"/croppy"+str(moverID)+"-*-*.fit",Stdout=FitsDir+"/croppies"+str(moverID)+".lis") 
				iraf.export.images="@"+FitsDir+"/croppies"+str(moverID)+".lis"
				iraf.export.format="gif"
				iraf.export.binfiles=CroppiesDir+"/croppies"+str(moverID)+".gif"
				iraf.export.outbands="band(  \
						zscale(i1)//128//zscale(i2)//128//zscale(i3),	\
						128, \
						zscale(i4)//128//zscale(i5)//128//zscale(i6),	\
						128, \
						zscale(i7)//128//zscale(i8)//128//zscale(i9)	\
						)"
				iraf.export()


	def images(self):
		tam=self.tam
		ImagesDir=self.ImagesDir
		FitsDir=self.FitsDir
		if not os.path.exists(FitsDir):
		    os.makedirs(FitsDir)
		res=commands.getoutput("rm "+FitsDir+"/image*" )
		movers=self.data
		moversIDs=set(movers['ID'])
		for moverID in moversIDs:
			#res=commands.getoutput("rm image"+str(moverID)+"*.fits" )
			print "Imaging mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			for id in mover['frame']:
				print "Processing frame:",id
				#SrcFrame=frame+"-%02u.fit" % int(id)
				#print "imagen SrcFrame:",SrcFrame
				SrcFrame=self.solvefits[int(id)-1]
				print "imagen SrcFrame:",SrcFrame
				moverFlt=(mover['frame']==id)
				mov=mover[moverFlt]
				x=int(float(mov['X_IMAGE'][0]))
				y=int(float(mov['Y_IMAGE'][0]))

				CropFrame=FitsDir+"/image%s-%02u.fit" % (moverID,int(id))
				if os.path.isfile(CropFrame):
					os.remove(CropFrame)
				self.cropper(SrcFrame,(x-tam,y-tam),(x+tam,y+tam),CropFrame)
   			
		
			if 1:				
				iraf.files(FitsDir+"/image"+str(moverID)+"-*.fit",Stdout=FitsDir+"/image"+str(moverID)+".lis") 
		   		#iraf.imcombine.combine="average"
				#iraf.imcombine.reject="sigclip"
		   		iraf.imcombine.combine="median"
				iraf.imcombine.reject="minmax"
				iraf.imcombine.nlow="0"
				iraf.imcombine.nhigh="2"
				iraf.imcombine.lsigma="1.01"
				iraf.imcombine.hsigma="1.01"
				iraf.imcombine.scale="none"
				iraf.imcombine.expname="EXPTIME"
				iraf.imcombine.offset="none"
				iraf.imcombine.weight="none"
				iraf.imcombine.zero="none"
				iraf.imcombine("@"+FitsDir+"/image"+str(moverID)+".lis",output=FitsDir+"/image"+str(moverID)+".fit")
				if not os.path.exists(ImagesDir):
				    os.makedirs(ImagesDir)
				res=commands.getoutput("rm "+ImagesDir+"/image"+str(moverID)+".gif" )
				
				iraf.export.images=FitsDir+"/image"+str(moverID)+".fit"
				#iraf.export.images="@image"+str(moverID)+".lis"
				iraf.export.format="gif"
				iraf.export.binfiles=ImagesDir+"/image"+str(moverID)+".gif"
				#iraf.export.outbands="zscalem(i1,i1>=0 &&i1<=255)"
				iraf.export.outbands="zscale(i1)"
				#iraf.export.outbands="cmap(i1,i2,i3)"
				iraf.export()


	def correlations(self):
		CorrelationDir=self.CorrelationDir
		if not os.path.exists(CorrelationDir):
			    os.makedirs(CorrelationDir)
		movers=self.data
		moversIDs=set(movers['ID'])
		margen=5
		for moverID in moversIDs:
			print "Correlation mover ID:",moverID
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			W0=float(mover['W[0]'][0])
			W1=float(mover['W[1]'][1])
			RAs=mover['ALPHA_J2000']
			DECs=mover['DELTA_J2000']
			DISTANCEs=mover['LINE_DIS']
			if 1:
				
				#upper rigth corner
				x0=min(RAs)*3600-margen
				y0=min(DECs)*3600-margen
				#lower left corner
				x1=max(RAs)*3600+margen
				y1=max(DECs)*3600+margen
				deltaX=x1-x0
				deltaY=y1-y0
				if deltaX>deltaY:
					ymean=(y0+y1)/2
					y0=ymean-deltaX/2
					y1=ymean+deltaX/2
				else:
					xmean=(x0+x1)/2
					x0=xmean-deltaY/2
					x1=xmean+deltaY/2
			# plotting the line
			line = (W0*RAs+W1)*3600 # regression line
			figure(figsize=(10,6), dpi=80)
			plot(RAs*3600,line,'r-',RAs*3600,DECs*3600,'o')
			#print axis()
			#print (x0,x1,y0,y1)
			axis((x0,x1,y0,y1))
			GOOD_DETECTION=mover['GOODFLAG'][0]
			for i,mover_frame in enumerate(mover['frame']):
				print "Processing frame:",i
				ra=RAs[i]
				dec=DECs[i]
				dis=DISTANCEs[i]
				annotate("GOOD_FLAG:"+str(GOOD_DETECTION),xy=(ra*3600,dec*3600), xycoords='data', textcoords='offset points')
				annotate(str(int(dis*100)/100.),xy=(ra*3600,dec*3600), xycoords='data', \
			        xytext=(+18, +18), textcoords='offset points', fontsize=10, \
			        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))

			savefig(CorrelationDir+"/correlation"+str(moverID)+".png")					

   			

			
			
	
	def contour(self):
		movers=self.data
		moversIDs=set(movers['ID'])
		res=commands.getoutput("rm *.eps" )
		ContourDir=self.ContourDir
		FitsDir=self.FitsDir
		if not os.path.exists(ContourDir):
			    os.makedirs(ContourDir)
		for moverID in moversIDs:
			print "Contour ID:",moverID
			filename=FitsDir+"/image"+str(moverID)+".fit"
			if os.path.isfile(filename):
				iraf.contour(filename,dev="eps")
				iraf.gflush()
				contourfile=glob.glob("*.eps")
				os.rename(contourfile[0],"contour"+str(moverID)+".eps")
				res=commands.getoutput("convert contour"+str(moverID)+".eps contour"+str(moverID)+".png" )
				res=commands.getoutput("mv contour"+str(moverID)+".png "+ContourDir )
				res=commands.getoutput("rm contour"+str(moverID)+".eps" )
			else:
				contourGif=ContourDir+"/contour"+str(moverID)+".png"
				res=commands.getoutput("cp "+self.htmldir+"/nodata.gif "+contourGif )

	def html(self):

		#flags de deteccion 
		LINE_GOOD_DETECTION=1
		MAG_GOOD_DETECTION=2
		SP_GOOD_DETECTION=4
		CORRELATION_GOOD_DETECTION=8
		MPC_GOOD_DETECTION=16
		MPC_MAG_GOOD_DETECTION=32
		REAL_DETECTION=64


		FitsDir=self.FitsDir.replace(self.htmldir,'.')
		ImagesDir=self.ImagesDir.replace(self.htmldir,'.')
		ContourDir=self.ContourDir.replace(self.htmldir,'.')
		AnimationDir=self.AnimationDir.replace(self.htmldir,'.')
		CroppiesDir=self.CroppiesDir.replace(self.htmldir,'.')
		CorrelationDir=self.CorrelationDir.replace(self.htmldir,'.')
		MapsDir=self.MapsDir.replace(self.htmldir,'.')+"/"
		print "Generando HTML",self.frame+".html"
		f=open(self.htmldir+"/"+self.frame+".html","w")
		f.write("<html><head></head><body>\n")
		f.write('<link rel="stylesheet" type="text/css" href="eetf.css" />\n')
		f.write("<h2>"+self.frame+"</h2>\n")
		movers=self.data
		movers=movers[movers['GOODFLAG'] >= self.moverMainFlt]
		#print movers
		moversIDs=set(movers['ID'])
		for moverID in moversIDs:
			moverFlt=(movers['ID']==moverID)
			mover=movers[moverFlt]
			f.write('<div class="moverTable">')
			f.write("<table>")
			f.write("<tr>")
			f.write("<td rowspan=4 width=30>")
			f.write("ID:"+str(moverID))
			f.write("</td>")
			f.write("<td>")
			f.write("RA: "+str(mover["RA"][0]))
			self.miniTable(f,[mover["RA"]])
			f.write("</td>")
			f.write("<td>")
			f.write("DEC: "+str(mover["DEC"][0]))
			self.miniTable(f,[mover["DEC"]])
			f.write("</td>")
			f.write("<td>")
			f.write("MEAN MAG "+str(round(mover["MEAN_MAG"][0],2)))
			self.miniTable(f,[mover["MAG_AUTO"]])
			f.write("</td>")
			f.write("<td>")
			f.write("FWHM: "+str(round(mover["FWHM"][0],2)))
			self.miniTable(f,[mover["FWHM"]])
			f.write("</td>")
			f.write("<td>")
			f.write("PA: "+str(round(mover["PA"][0],0)))
			f.write("</td>")
			f.write("<td>")
			f.write("SPD: "+str(round(mover["MEANspeed"][0],2)))
			self.miniTable(f,[mover["speed"]])
			f.write("</td>")
			f.write("<td>")
			f.write("CORRE:"+"%0.2e" % float(mover["CORRELATION"][0]))
			self.miniTable(f,[mover["LINE_DIS"]])
			f.write("</td>")
			if mover["GOODFLAG"][0] & REAL_DETECTION :
				f.write("<td style=\"color:lime\" rowspan=4 width=30>")
				f.write("REAL")
			else:
				f.write("<td style=\"color:grey\" rowspan=4 width=30>")
				f.write("FALSE")
			if mover["GOODFLAG"][0] & MPC_GOOD_DETECTION and mover["GOODFLAG"][0] & MPC_MAG_GOOD_DETECTION:
				f.write("<br>EXISTING")
			else:
				f.write("<br style=\"color:red\">NEW</</br>")
			f.write("</td>")
			f.write("</tr>")
			if 1:

				f.write("<tr>")
				f.write("<td  style=\"background-color:#cccccc\">")
				f.write("FLAGS:")
				f.write("</td>")
				if mover["GOODFLAG"][0] & LINE_GOOD_DETECTION :
					f.write("<td  style=\"background-color:lime\">")
					f.write("ALIGNED1")
				else:
					f.write("<td>")
					f.write("NOT ALIGNED1")
				f.write("</td>")
				if mover["GOODFLAG"][0] & CORRELATION_GOOD_DETECTION :
					f.write("<td  style=\"background-color:lime\">")
					f.write("ALIGNED2")
				else:
					f.write("<td>")
					f.write("NOT ALIGNED2")
				f.write("</td>")

				if mover["GOODFLAG"][0] & MAG_GOOD_DETECTION :
					f.write("<td  style=\"background-color:lime\">")
					f.write("SIMIL.MAG")
				else:
					f.write("<td>")
					f.write("NOT SIMIL.MAG")
				f.write("</td>")
				if mover["GOODFLAG"][0] & SP_GOOD_DETECTION :
					f.write("<td  style=\"background-color:lime\">")
					f.write("SIMIL.SPD")
				else:
					f.write("<td>")
					f.write("NOT SIMIL.SPD")
				f.write("</td>")
				if mover["GOODFLAG"][0] &  MPC_GOOD_DETECTION :
					f.write("<td  style=\"background-color:lime\">")
					f.write("MATCH MPC")
				else:
					f.write("<td  style=\"background-color:red\">")
					f.write("NOT MATCH MPC")
				f.write("</td>")
				if mover["GOODFLAG"][0] & MPC_MAG_GOOD_DETECTION :
					f.write("<td  style=\"background-color:lime\">")
					f.write("SAME MPC MAG")
				else:
					f.write("<td  style=\"background-color:red\">")
					f.write("NOT SAME MPC MAG")
				f.write("</td>")
				f.write("</tr>")

			if 1:
				f.write("<tr>")
				f.write("<td  style=\"background-color:#cccccc\">")
				f.write("MPC: ")
				f.write("</td>")
				f.write("<td>")
				f.write("KEY: "+str(mover["KEY_MPC"][0]))
				f.write("</td>")
				f.write("<td>")
				f.write("MATCH_DIS: "+str(round(mover["DIS_MPC"][0],2)))
				f.write("</td>")
				f.write("<td>")
				f.write("MAG: "+str(round(mover["MAG_MPC"][0],2)))
				f.write("</td>")
				f.write("<td>")
				f.write("EARTH_DIS: "+str(round(mover["EARTH_DIS_MPC"][0],2)))
				f.write("</td>")
				f.write("<td>")
				f.write("PHASE: "+str(round(mover["PHASE_MPC"][0],2)))
				f.write("</td>")
				f.write("<td>")
				f.write("ELONG: "+str(round(mover["ELONG_MPC"][0],2)))
				f.write("</td>")
				f.write("</tr>")


			f.write("<td>\n")
			f.write('\n<a class="thumbnail" href="#thumb"><img src=\"'+ImagesDir+'/image'+str(moverID)+'.gif"  width=150 height=150 border="1" /><span><img src=\"'+ImagesDir+'/image'+str(moverID)+'.gif" width=300 height=300 /></span></a>\n')
			#f.write("<image class=\"fancy\" width=150 height=150 src=\"./images/image"+str(moverID)+".gif\">")
			f.write("</td>\n")
			f.write("<td>\n")
			f.write('\n<a class="thumbnail" href="#thumb"><img src=\"'+ContourDir+'/contour'+str(moverID)+'.png"  width=150 height=150 border="1" /><span><img src=\"'+ContourDir+'/contour'+str(moverID)+'.png" width=600 height=400 /></span></a>\n')
			#f.write("<image src=\"./contour"+str(moverID)+".png\">\n")
			f.write("</td>\n")
			f.write("<td>\n")
			f.write('\n<a class="thumbnail" href="#thumb"><img src=\"'+CorrelationDir+'/correlation'+str(moverID)+'.png"  width=150 height=150 border="1" /><span><img src=\"'+CorrelationDir+'/correlation'+str(moverID)+'.png" width=600 height=400 /></span></a>\n')
			#f.write("<image src=\"./contour"+str(moverID)+".png\">\n")
			f.write("</td>\n")
			f.write("<td>\n")
			f.write('\n<a class="thumbnail" href="#thumb"><img src=\"'+AnimationDir+'/animate-'+'%02u' % moverID+'.gif" width=150 height=150   border="1" /><span><img src=\"'+AnimationDir+'/animate-'+'%02u' % moverID+'.gif" width=300 height=300 /></span></a>\n')
			#f.write("<image width=150 height=150 src=\"./animations/animate-"+"%02u" % moverID+".gif\">\n")
			f.write("</td>\n")
			f.write("<td>\n")
			f.write('\n<a class="thumbnail" href="#thumb"><img src=\"'+CroppiesDir+'/croppies'+str(moverID)+'.gif" width=150 height=150  border="1" /><span><img src=\"'+CroppiesDir+'/croppies'+str(moverID)+'.gif" width=300 height=300 /></span></a>\n')
			#f.write("<image width=150 height=150 src=\"./croppies/croppies"+str(moverID)+".gif\">\n")
			f.write("</td>\n")
			f.write("</tr>\n")
			f.write("</table>\n")
			f.write('</div>')
			f.write('<p>')
		f.write("</body></html>")
		f.close()
		res=commands.getoutput("ln -s "+self.htmldir+"/"+self.frame+".html "+self.htmldir+"/index.html")

	def miniTable(self,f,data):
		#print data
		f.write("<div class=\"mag\">")
		f.write("<table>")
		for row in data:
			for col in row:
				f.write("<tr >")
				f.write("<td >")
				f.write(str(col))
				f.write("</td>")
				f.write("</tr>")
		f.write("</table>")
		f.write("</div>")


	def maps(self):
		MapsDir=self.MapsDir
		if not os.path.exists(MapsDir):
			    os.makedirs(MapsDir)
         	Cmd="stilts plot2d xpix=1500 ypix=850 in2=Gcandidates_"+self.frame+".cat xdata2=ALPHA_J2000 \
		ydata2=DELTA_J2000 shape2=filled_square size2=5 colour2=red auxshader=rainbow auxlog=true out="+MapsDir+"/"+self.frame+"_map1.png \
		in1=astPos.cat shape1=open_circle xdata1=RA ydata1=DEC auxdata1=PHASE subset1='MAG<20' transparency1=5 size1=0"
		res=commands.getoutput(Cmd)
		print res
		movers=self.data
		margen=0.5
		RAmax=max(movers['ALPHA_J2000'])+margen
		DECmax=max(movers['DELTA_J2000'])+margen
		RAmin=min(movers['ALPHA_J2000'])-margen
		DECmin=min(movers['DELTA_J2000'])-margen
         	Cmd="stilts plot2d xpix=1500 ypix=850   out="+MapsDir+"/"+self.frame+"_map2.png \
		in1=Gcandidates_"+self.frame+".cat shape1=cross xdata1=ALPHA_J2000 ydata1=DELTA_J2000 size1=5 subset1='frame==1' txtlabel1=ID \
		in2=astPos.cat xdata2=RA ydata2=DEC xlo="+str(RAmin)+" xhi="+str(RAmax)+" ylo="+str(DECmin)+" yhi="+str(DECmax) \
		+" shape2=open_square size2=3 colour2=green subset2='MAG<=20'"

		res=commands.getoutput(Cmd)
		print res
		
		






if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	cropp=cropClass(fitsFiles)
	cropp.do()



