"""NASA/JPL Horizons observer table client; data are requested live, never fabricated."""
import csv
import io
import re
import json
from pathlib import Path
from datetime import date, timedelta
import requests

API = 'https://ssd.jpl.nasa.gov/api/horizons.api'

class HorizonsError(RuntimeError):
    pass

def get_observer_ephemeris(target: str, lat: float, lon: float, start: date, days: int = 5, step: str = '2h', capture_dir=None):
    """Target 10 Sun or 399 Earth. Return UTC timestamp, azimuth/elevation degrees.

    Uses an airless local horizontal coordinate system and geometric local horizon.
    """
    if target not in ('10', '399'):
        raise ValueError('Target must be Sun (10) or Earth (399)')
    if not -90 <= lat <= 90 or not -180 <= lon <= 360:
        raise ValueError('Invalid lunar coordinates')
    if days < 1 or days > 31:
        raise ValueError('days must be 1–31')
    p = {
        'format': 'json', 'COMMAND': f"'{target}'", 'MAKE_EPHEM': "'YES'",
        'EPHEM_TYPE': "'OBSERVER'", 'OBJ_DATA': "'NO'",
        'CENTER': "'coord@301'", 'COORD_TYPE': "'GEODETIC'",
        'SITE_COORD': f"'{lon % 360:.6f},{lat:.6f},0'",
        'START_TIME': f"'{start.isoformat()}'",
        'STOP_TIME': f"'{(start + timedelta(days=days)).isoformat()}'",
        'STEP_SIZE': f"'{step}'", 'QUANTITIES': "'4'",
        'CSV_FORMAT': "'YES'", 'ANG_FORMAT': "'DEG'", 'APPARENT': "'AIRLESS'",
        'TIME_TYPE': "'UT'", 'TIME_DIGITS': "'MINUTES'",
    }
    try:
        resp = requests.get(API, params=p, timeout=40)
        resp.raise_for_status()
        body = resp.json().get('result', '')
        if capture_dir is not None:
            directory = Path(capture_dir)
            directory.mkdir(parents=True, exist_ok=True)
            tag = f"{'sun' if target=='10' else 'earth'}_{lat:+08.4f}_{lon:+09.4f}_{start.isoformat()}"
            (directory / (tag + '.raw.txt')).write_text(body, encoding='utf-8')
            (directory / (tag + '.request.json')).write_text(json.dumps({'source': API, 'request_parameters': p, 'request_url': resp.url, 'raw_file': tag + '.raw.txt'}, indent=2), encoding='utf-8')
    except (requests.RequestException, ValueError) as exc:
        raise HorizonsError(f'Unable to retrieve JPL Horizons data: {exc}') from exc
    if '$$SOE' not in body or '$$EOE' not in body:
        raise HorizonsError('Horizons did not return an ephemeris table: ' + body[-900:])
    raw = body.split('$$SOE', 1)[1].split('$$EOE', 1)[0]
    points = []
    for parts in csv.reader(io.StringIO(raw)):
        fields = [x.strip() for x in parts if x.strip()]
        if len(fields) < 3:
            continue
        # CSV_FORMAT=YES with QUANTITIES=4: date, visibility marker, azimuth, elevation.
        # Marker can be empty, 'm', '*', or other tokens depending on target.
        # Use trailing two numeric fields, not an assumed fixed index.
        numbers = []
        for field in fields[1:]:
            try:
                numbers.append(float(field))
            except ValueError:
                pass
        if len(numbers) < 2:
            continue
        # Q4 prints azimuth followed by elevation; trailing punctuation already filtered.
        az, el = numbers[-2:]
        if not (0 <= az <= 360 and -90 <= el <= 90):
            continue
        timestamp = fields[0].replace('A.D.', '').strip()
        # Horizons uses 2026-Nov-14 00:00 for calendar dates
        from datetime import datetime, timezone
        match = re.search(r'(\d{4}-[A-Za-z]{3}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)', timestamp)
        if not match:
            continue
        fmt = '%Y-%b-%d %H:%M:%S' if match.group(1).count(':') == 2 else '%Y-%b-%d %H:%M'
        dt = datetime.strptime(match.group(1), fmt).replace(tzinfo=timezone.utc)
        points.append({'time': dt, 'az': az, 'el': el})
    if len(points) < 2:
        raise HorizonsError('Horizons responded, but its observer table could not be parsed. Inspect raw API output/format.')
    if len(set(point['time'] for point in points)) != len(points):
        raise HorizonsError('Horizons output contains duplicated timestamps')
    from datetime import datetime, timezone
    expected_first=datetime.combine(start,datetime.min.time(),tzinfo=timezone.utc)
    expected_last=expected_first+timedelta(days=days)
    if points[0]['time'] != expected_first or points[-1]['time'] != expected_last:
        raise HorizonsError('Ephemeris coverage incomplete: expected start and end UTC timestamps. Check Horizons response.')
    if any(points[i]['time'] >= points[i+1]['time'] for i in range(len(points)-1)):
        raise HorizonsError('Horizons output timestamps not strictly increasing')
    return points
