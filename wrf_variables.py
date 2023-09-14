#!/usr/bin/env python
"""wrf_variables.py methods
Author: Daniel Argueso (d.argueso@unsw.edu.au) at CoECSS, UNSW, and CCRC, UNSW. Australia.

Methods to calculate variables derived from WRF standard/postprocessed output. Standard NARCliM outputs.

Created: 08 August 2013
Modified: Mon Aug  4 16:15:48 EST 2014: Added computation of moist adiabatic lapse rate (dT/dP)

"""
from constants import const
import numpy as np
import netCDF4 as nc
import datetime as dt
import sys
import pdb

def compute_e(psfc,q2):
    """Function to calculate vapour pressure from:
       psfc: surface pressure (assumed the same at 2m) [Pa]
       q2: 2-m mixing ratio [kg kg-1]
       ---
       e: vapor pressure [Pa]
    """

    e = q2*psfc/((const.epsilon_gamma+q2))

    return e

def compute_es(t2):
    """Function to calculate saturated vapour pressure from:
       t2: 2m temperature [K]
       ---
       es: saturated vapor pressure [Pa]
    """
    es = np.where(
        t2-const.tkelvin <=0.,
        const.es_base_tetens*10.**(((t2-const.tkelvin)*const.es_Atetens_ice)/
        ((t2-const.tkelvin)+const.es_Btetens_ice)), #ICE
        const.es_base_tetens*10.**(((t2-const.tkelvin)*const.es_Atetens_vapor)/
          ((t2-const.tkelvin)+const.es_Btetens_vapor))) #(else) Vapor
    return es

def compute_RH2(psfc,t2,q2):
    """Function to calculate relative humidity at 2 m from:
        psfc: surface pressure (assumed the same at 2m) [Pa]
        q2: 2-m mixing ratio [kg kg-1]
        t2: 2m temperature [K]
        ---
        rh2: relative humidity
    """
    e = q2*psfc/(100.*(const.epsilon_gamma+q2)) #e in hPA
    es = np.where(
        t2-const.tkelvin <=0.,
        const.es_base_tetens*10.**(((t2-const.tkelvin)*const.es_Atetens_ice)/
        ((t2-const.tkelvin)+const.es_Btetens_ice)), #ICE
        const.es_base_tetens*10.**(((t2-const.tkelvin)*const.es_Atetens_vapor)/
          ((t2-const.tkelvin)+const.es_Btetens_vapor))) #(else) Vapor
    rh2=(e/es)*100

    return rh2

def compute_VPD(psfc,t2,q2):
    """Function to calculate vapor pressure deficit from:
       psfc: surface pressure (assumed the same at 2m) [Pa]
       t2: 2m temperature [K]
       q2: 2-m mixing ratio [kg kg-1]
       ---
       VPD: vapor pressure deficit [Pa]
    """

    es = np.where(
        t2-const.tkelvin <=0.,
        const.es_base_tetens*10.**(((t2-const.tkelvin)*const.es_Atetens_ice)/
        ((t2-const.tkelvin)+const.es_Btetens_ice)), #ICE
        const.es_base_tetens*10.**(((t2-const.tkelvin)*const.es_Atetens_vapor)/
          ((t2-const.tkelvin)+const.es_Btetens_vapor))) #(else) Vapor
    e = q2*psfc/(100.*(const.epsilon_gamma+q2))
    VPD=es-e
    return VPD


def compute_WBGT(t2,e):
    """Function to calculate simplified wet-bulb globe temperature from:
       t2: 2m temperature [K]
       e: vapor pressure [Pa]
       ---
       w2: wet-bulb temperature

       Fischer et al. 2012 GRL
    """

    w2=0.567*(t2-const.tkelvin) + 0.393*e/100. +3.94

    return w2


def compute_AT(t2,e,ws):
    """Function to calculate Apparent Temperature (Steadman,1994) from:
       t2: 2m temperature [K]
       e: vapor pressure [Pa]
       ws: wind speed [m s-1]
       ---
       at2: apparent temperature [equiv degC]
    """

    at2=(t2-const.tkelvin)+0.33*e/100.-0.7*ws+4.0

    return at2


def compute_precPDF(prec,min_p=0.0,max_p=200.,bins_p=100,thres_p=0.0):
    """Function to calculate the PDF for precipitation (postprocessed)
       prec: precipitation (both convective and non-convective) (time,lat/lon,lon/lat) [mm]
       min:  minimum precipitation in the PDF (default=0.0) [mm]
       max:  maximum precipitation in the PDF (default=200.) [mm]
       bins: number of bins between min and max (default=100) [mm]
       thres_p: threshold to consider a day wet. [mm]
       ---
       pdf: probability distribution function (PDF)
       pseudo_pdf: contribution to total annual precipitation [mm/year]
       edges: edges of the bins used to classify events [mm]
    """
    hist=np.zeros((bins_p,)+prec.shape[1:],dtype=np.float64)
    pdf=np.zeros((bins_p,)+prec.shape[1:],dtype=np.float64)
    pseudo_pdf=np.zeros((bins_p,)+prec.shape[1:],dtype=np.float64)
    prec=np.ma.masked_less_equal(prec[:],thres_p)
    for i in xrange(prec.shape[1]):
        for j in xrange(prec.shape[2]):
            hist[:,i,j], edges= np.histogram(prec[:,i,j].compressed(),bins=bins_p,range=(min_p,max_p))
            pseudo_pdf[:,i,j]=hist[:,i,j]*(edges[:-1]+(edges[1]-edges[0])/2.)/float(prec.shape[0]/365.25)
    events=np.sum(hist,0)
    events[events==0]=1

    for ii in xrange(hist.shape[0]):
        pdf[ii,:,:]=np.squeeze(hist[ii,:,:])/events[:,:]

    return pdf,pseudo_pdf,edges

def compute_prec(files):
    """Function to calculate preciptiation from accumulated rainnc and rainc (if applicable)
        It provides accumualted precipitation for every timestep (as opposed to the continuous accumulated rain provided in wrf files)
        files: list of files containing precipitation (RAINNC is compulsory, RAINC optional)
        ---
        pracc: accumulated precipitation for every timestep
    """
    x=[]
    for fname in files:
    	fin=nc.Dataset(fname,mode='r')
    	rainnc=fin.variables['RAINNC'][:]
    	if 'RAINC' in fin.variables:
    	    rainc=fin.variables['RAINC'][:]
    	    xFragment=rainc+rainnc
    	else:
    	    xFragment=rainnc
    	x.append(xFragment)

    #Concatenates  precipitation variables from all input files and calculates the difference between each timestep.
    pracc=np.diff(np.squeeze(np.concatenate(x,axis=0)),axis=0)

    return pracc

def compute_gamma_s(T,p):
  """Calculates moist adiabatic lapse rate for T (Celsius) and p (Pa)
  Note: We calculate dT/dp, not dT/dz
  See formula 3.16 in Rogers&Yau for dT/dz, but this must be combined with
  the dry adiabatic lapse rate (gamma = g/cp) and the
  inverse of the hydrostatic equation (dz/dp = -RT/pg)
  From pywrfplot by Geir Arne Waagboe. see http://code.google.com/p/pywrfplot/
  T: temperature [k]
  p: pressure [Pa]
  ---
  gamma: moist adiabatic lapse rate [K/Pa]
  """

  esat=compute_es(T)
  wsat=const.epsilon_gamma*esat(p-esat) # Rogers&Yau 2.18
  numer=const.a*T + const.c*wsat
  denom=p * (1 + const.b*wsat/T**2)
  gamma=numer/denom # Rogers&Yau 3.16
  return gamma

def compute_Tdew(e):
  """Calculates dew point temperature at vapor pressure e
     e: vapor pressure [Pa]
     ---
     Tdew: dew point temperature [K]
  """

  Tdew = const.es_Bbolton * np.log(e/const.es_base_bolton)/(const.es_Abolton-np.log(e/const.es_base_bolton)) + const.tkelvin

  return Tdew

# def compute_div(u,v,lon,lat):


#     ###### Needs revision...it is not working right now....#######


#     """Function to calculate wind divergence
#        u:zonal wind [m s-1]
#        v:meridional wind [m s-1]
#        lon: longitude [degrees_east]
#        lat: latitude [degrees_north]
#        ---
#        dv: divergence [s-1]
#
#        Divergence calcualted according to H.B. Bluestein [Synoptic-Dynamic Meteorology in Midlatitudes, 1992, Oxford Univ. Press p113-114]
#        and https://www.ncl.ucar.edu/Document/Functions/Built-in/uv2dv_cfd.shtml
#
#        Author: Daniel Argueso @ CCRC, UNSW. Sydney (Australia)
#        Created: Sat Mar  7 23:49:32 AEDT 2015
#
#     """
#
#     dv = np.ones((u.shape[0],) + (u.shape[1],) + (u.shape[2],),dtype=np.float64)*const.missingval
#
#     dx2 = np.resize(np.abs(lon[1:-1,2:] - lon[1:-1,:-2]),(u.shape[0],u.shape[1]-2,u.shape[2]-2))
#     dy2 = np.resize(np.abs(lat[2:,1:-1] - lon[:-2,1:-1]),(u.shape[0],u.shape[1]-2,u.shape[2]-2))
#
#     dv[:,1:-1,1:-1] = ((v[:,2:,1:-1]-v[:,:-2,1:-1])/dy2 +
#          (u[:,1:-1,2:]-u[:,1:-1,:-2])/dx2 +
#          -(v[:,1:-1,1:-1]/const.earth_radius)*np.tan(lat[1:-1,1:-1]))
#
#     return dv

def compute_div_dx(u,v,dx,dy):
  """Function to calculate wind divergence providing the distance between grid points only
     u:zonal wind [m s-1]
     v:meridional wind [m s-1]
     dx: distance between gridpoints longitudinal [m]
     dy: distance between gridpoints latitudinal [m]
     ---
     dv: divergence [s-1]

     Author: Daniel Argueso @ CCRC, UNSW. Sydney (Australia)
     Created: Mon Mar  9 11:42:51 AEDT 2015 based on compute_div

  """

  dv = np.zeros((u.shape[0],) + (u.shape[1],) + (u.shape[2],),dtype=np.float64)

  dv[:,1:-1,1:-1] = (u[:,1:-1,2:]-u[:,1:-1,:-2])/(2*dx) + (v[:,2:,1:-1]-v[:,:-2,1:-1])/(2*dy)

  return dv
