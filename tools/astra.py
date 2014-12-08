#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import ephem
import numpy as np

f=open('astrometry2.txt','r')
lon = -2.565645
lat = 37.982619
hor=0
here = ephem.Observer()
here.lat, here.lon, here.horizon  = str(lat), str(lon), str(hor)
here.elev = float(1531)

for w in f:
	data=w.split(' ')
	dd=float(data[3])
	day=int(dd)
	hh=(dd-day)*24*60*60
	hour=int(hh/3600)
	minute=int((hh-hour*3600)/60)
	second=int((hh-hour*3600-minute*60))
	#print data[3],day,hour,minute,second
	time=data[1]+"/"+data[2]+"/"+str(day)+" "+str(hour)+":"+str(minute)+":"+str(second)
	d = ephem.Date(time)
	here.date=d
	ra=data[4]
	dec=data[5]
	#ra, dec = here.radec_of(ra, dec)
	astra = ephem.FixedBody()
	astra._ra = ephem.hours(ra)
	astra._dec = ephem.degrees(dec)
	astra.compute(here)
	print d,ephem.julian_date(d),ra,dec,float(astra.alt)*180/np.pi, float(astra.az)*180/np.pi


