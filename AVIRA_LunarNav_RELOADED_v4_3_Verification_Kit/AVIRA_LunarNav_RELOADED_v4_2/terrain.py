"""Azimuth-indexed horizon profile and a GeoTIFF-DEM-derived approximate local horizon.
GeoTIFF path relies on optional rasterio; the file must be a lunar south-polar projected
DEM whose pixel units and elevation units are METERS (e.g. LOLA PGDA products).
"""
import io
import math
import numpy as np
import pandas as pd

class TerrainError(ValueError):
    pass

def read_horizon_csv(file_or_bytes):
    """CSV: azimuth_deg,elevation_deg. Must cover 0..360 by wrapping; interpolation cyclic."""
    df=pd.read_csv(io.BytesIO(file_or_bytes) if isinstance(file_or_bytes,bytes) else file_or_bytes)
    if not {'azimuth_deg','elevation_deg'}.issubset(df.columns):
        raise TerrainError('CSV requires azimuth_deg,elevation_deg columns')
    vals=df[['azimuth_deg','elevation_deg']].apply(pd.to_numeric,errors='coerce')
    if vals.isna().any().any() or len(vals)<8:
        raise TerrainError('At least eight finite azimuth/elevation rows required')
    az=vals.azimuth_deg.to_numpy(dtype=float)%360.
    el=vals.elevation_deg.to_numpy(dtype=float)
    if (np.abs(el)>90).any():
        raise TerrainError('Horizon elevation outside +/-90 degrees')
    if len(np.unique(az)) != len(az):
        raise TerrainError('Duplicate azimuths in terrain profile')
    order=np.argsort(az)
    az,el=az[order],el[order]
    gaps=np.diff(np.r_[az,az[0]+360.])
    if gaps.max() > 60:
        raise TerrainError('Azimuth coverage has a gap above 60 degrees')
    def horizon(heading):
        return float(np.interp(float(heading)%360,np.r_[az[-1]-360,az,az[0]+360],np.r_[el[-1],el,el[0]]))
    return horizon, pd.DataFrame({'azimuth_deg':az,'elevation_deg':el})

def derive_horizon_dem(tif_path,site_x,site_y,az_step=5.,max_range_m=15000.,step_m=150.,lander_height_m=1.5):
    """Approximate terrain mask from meters-based projected DEM using rasterio.
    Horizon convention: azimuth 0=north, 90=east, elevation above local horizontal.
    No geodetic conversion or Moon curvature correction: limited-distance sensitivity model.
    Missing/no-data rays FAIL CLOSED rather than becoming flat horizon.
    """
    try:
        import rasterio
    except ImportError as exc:
        raise TerrainError('Install optional rasterio to load a NASA LOLA GeoTIFF') from exc
    if not 0 < az_step <= 45 or not 0 < step_m <= max_range_m or max_range_m > 100000:
        raise TerrainError('Invalid resolution or horizon radius')
    with rasterio.open(tif_path) as src:
        if not src.crs or src.crs.is_geographic:
            raise TerrainError('Expected projected lunar GeoTIFF with meter coordinates')
        if any(abs(x)>0.01 for x in src.res):
            pass
        # src.sample respects affine transforms; explicit fail on nodata/masked.
        coords=[(site_x,site_y)]
        azs=np.arange(0,360,az_step)
        ranges=np.arange(step_m,max_range_m+step_m/2,step_m)
        for az in azs:
            theta=np.radians(az)
            coords += [(site_x+r*np.sin(theta),site_y+r*np.cos(theta)) for r in ranges]
        vals=np.array([v[0] for v in src.sample(coords,masked=True)],dtype=object)
        # Re-read as float and preserve masked entries.
        zz=np.ma.array([v[0] for v in src.sample(coords,masked=True)])
        if np.ma.getmaskarray(zz).any() or not np.all(np.isfinite(np.asarray(zz,dtype=float))):
            raise TerrainError('DEM nodata/off-map ray detected. Choose shorter range or another site')
        z0=float(zz[0])+lander_height_m
        zz=np.asarray(zz[1:],dtype=float).reshape(len(azs),len(ranges))
        # Spherical Moon curvature drops tangent-relative terrain by r^2/(2R).
        R=1737400.
        ang=np.degrees(np.arctan2(zz-z0-ranges[np.newaxis,:]**2/(2*R),ranges[np.newaxis,:]))
        heights=np.maximum(0.,np.max(ang,axis=1))
        df=pd.DataFrame({'azimuth_deg':azs,'elevation_deg':heights})
        output=io.StringIO();df.to_csv(output,index=False)
        h,_=read_horizon_csv(output.getvalue().encode())
        return h,df
