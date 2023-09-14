subroutine writeint(plvs,fields3d,fields2d,hdate,nLats,nLons,startlat,startlon,deltalon,deltalat)

!-----------------------------
!output the variables in intermediate format
!------------------------------

IMPLICIT NONE

!********** user modified variables *************
!
character (len=5), parameter :: ofname = "ERA5"
integer, parameter :: version = 5 ! Format version (must =5 for WPS format)
integer, parameter :: iproj = 0 ! Code for projection of data in array:
				! 0 = cylindrical equidistant
				! 1 = Mercator
				! 3 = Lambert conformal conic
				! 4 = Gaussian (global only!)
				! 5 = Polar stereographic
character (len=8), parameter :: startloc = "SWCORNER" ! Which point in array is given by
				! startlat/startlon; set either
				! to 'SWCORNER' or 'CENTER '
character (len=32), parameter :: map_source = "ERA5"! Source model / originating center
logical, parameter :: is_wind_grid_rel = .FALSE. ! Flag indicating whether winds are
				! relative to source grid (TRUE) or
				! relative to earth (FALSE)
real, parameter :: earth_radius = 6367.470215 ! Earth radius, km
					!this is average not from model


!******************************************************
!From toInterData
integer :: nLons, nLats ! x- and y-dimensions of 2-d array

real :: startlat, startlon ! Lat/lon of point in array indicated by
! startloc string
real :: deltalon,deltalat ! Grid spacing, degrees
!*******************************************************




real :: xfcst ! Forecast hour of data
real :: xlvl ! Vertical level of data in 2-d array
real,dimension(nLons,nLats) :: slab ! The 2-d array holding the data
real, dimension(:,:,:,:) :: fields3d !The array holding all 3-d variables
real, dimension(:,:,:) :: fields2d !The array holding all 3-d variables
real, dimension(:) :: plvs ! List of levels

character (len=9) :: field ! Name of the field
character (len=24) :: hdate ! Valid date for data YYYY:MM:DD_HH:00:00
character (len=25) :: units ! Units of data
character (len=46) :: desc ! Short description of data
character (len=46) :: fields3d_desc(5),fields2d_desc(7)
character (len=25) :: fields3d_units(5),fields2d_units(7)
character (len=9)  :: fields3d_name(5), fields2d_name(7)


integer :: ounit !output file
integer :: status,nf,nl,nfields3d,nfields2d
!local unused arguments


!f2py intent(in) ::plvs,fields3d,fields2d,hdate,nLats,nLons,startlat,startlon,deltalon

nfields3d=size(fields3d,1)
nfields2d=size(fields2d,1)

fields3d_name(1) = 'RH       '
fields3d_name(2) = 'TT       '
fields3d_name(3) = 'UU       '
fields3d_name(4) = 'VV       '
fields3d_name(5) = 'GHT      '

fields3d_units(1) = 'percent                  '
fields3d_units(2) = 'K                        '
fields3d_units(3) = 'm s-1                    '
fields3d_units(4) = 'm s-1                    '
fields3d_units(5) = 'm                        '

fields3d_desc(1) = 'Relative Humidity                           '
fields3d_desc(2) = 'Temperature                                 '
fields3d_desc(3) = 'U                                           '
fields3d_desc(4) = 'V                                           '
fields3d_desc(5) = 'Height                                      '

fields2d_name(1) = 'UU       '
fields2d_name(2) = 'VV       '
fields2d_name(3) = 'RH       '
fields2d_name(4) = 'PSFC     '
fields2d_name(5) = 'PMSL     '
fields2d_name(6) = 'TT       '
fields2d_name(7) = 'SKINTEMP '

fields2d_units(1) = 'm s-1                    '
fields2d_units(2) = 'm s-1                    '
fields2d_units(3) = 'percent                  '
fields2d_units(4) = 'Pa                       '
fields2d_units(5) = 'Pa                       '
fields2d_units(6) = 'K                        '
fields2d_units(7) = 'K                        '

fields2d_desc(1) = 'U                                           '
fields2d_desc(2) = 'V                                           '
fields2d_desc(3) = 'Relative Humidity                           '
fields2d_desc(4) = 'Surface Pressure                            '
fields2d_desc(5) = 'Sea-level pressure                          '
fields2d_desc(6) = 'Temperature                                 '
fields2d_desc(7) = 'Sea-Surface Temperature                     '



xfcst = 0.0 ! In the case of GCM is 0 hours
ounit=11

open(ounit,file="./"//TRIM(ofname)//":"//hdate(1:13),form='unformatted',IOSTAT=status,convert="BIG_ENDIAN")
if (status /= 0) then
  print *,"could not create ./"//TRIM(ofname)//':'//hdate(1:13)
  stop
endif

print *, "./"//TRIM(ofname)//":"//hdate(1:13)

!########## 3-D FIELDS ###############

do nf = 1,nfields3d
  do nl = 1,size(plvs)
    xlvl=plvs(nl)
    field = fields3d_name(nf)
    units = fields3d_units(nf)
    desc  = fields3d_desc(nf)
    slab = TRANSPOSE(fields3d(nf,nl,:,:))
!print *,field

write(unit=ounit) version

write(unit=ounit) hdate, xfcst, map_source, field, &
units, desc, xlvl, nLons, nLats, iproj


write(unit=ounit) startloc, startlat, startlon, &
deltalat, deltalon, earth_radius


! 3) WRITE WIND ROTATION FLAG
write(unit=ounit) is_wind_grid_rel

! 4) WRITE 2-D ARRAY OF DATA
write(unit=ounit) slab
  end do
end do

!########## 2-D FIELDS ###############

do nf = 1,nfields2d

  xlvl = 200100.0
  if (fields2d_name(nf).eq.'PMSL') xlvl=201300.0
  field = fields2d_name(nf)
  units = fields2d_units(nf)
  desc  = fields2d_desc(nf)
  slab = TRANSPOSE(fields2d(nf,:,:))


  write(unit=ounit) version

  write(unit=ounit) hdate, xfcst, map_source, field, &
  units, desc, xlvl, nLons, nLats, iproj
  write(unit=ounit) startloc, startlat, startlon, &
  deltalat, deltalon, earth_radius

  ! 3) WRITE WIND ROTATION FLAG
  write(unit=ounit) is_wind_grid_rel
  ! 4) WRITE 2-D ARRAY OF DATA
  write(unit=ounit) slab

end do
close(ounit)
return
END SUBROUTINE
