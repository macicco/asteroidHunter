#!/usr/bin/python
# -*- coding: iso-8859-15 -*-



import commands,os, sys

from eUconfig import *

cfg=dict(config.items("SWARP"))

class swarp(helper):
	def do(self):
		lista=""
		for i,fit in enumerate(self.solvefits):
			lista=lista+" "+fit

		swarpStr="swarp -c "+cfg["swarpcfg"]+lista+ " -IMAGEOUT_NAME "+self.frame+".fit "+\
		" -WEIGHTOUT_NAME  " +self.frame+".weight.fit "
		print "EXECUTING:\n",swarpStr
		res=commands.getoutput(swarpStr)
		print res

if __name__ == '__main__':
	fitsFiles=sys.argv[1:]
	swarp=swarp(fitsFiles)
	swarp.do()
