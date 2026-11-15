from datetime import date
from unittest.mock import patch
from pathlib import Path
import json
from horizons import get_observer_ephemeris

class FakeResponse:
    url='https://ssd.jpl.nasa.gov/api/horizons.api?mock=1'
    def raise_for_status(self): pass
    def json(self):
        return {'result': 'MOCKED-NOT-NASA\n$$SOE\n2026-Nov-15 00:00, , 45.0, +4.0,\n2026-Nov-15 12:00, , 46.0, +2.5,\n2026-Nov-16 00:00, , 48.0, -3.0,\n$$EOE\n'}

def test_capture_writes_raw_and_request(tmp_path):
    with patch('horizons.requests.get',return_value=FakeResponse()):
        points=get_observer_ephemeris('10',-89.5,0,date(2026,11,15),days=1,step='12h',capture_dir=tmp_path)
    raws=list(tmp_path.glob('*.raw.txt'))
    meta=list(tmp_path.glob('*.request.json'))
    assert len(raws)==len(meta)==1
    assert len(points)==3
    assert 'MOCKED-NOT-NASA' in raws[0].read_text()
    assert json.loads(meta[0].read_text())['request_parameters']['CENTER']=="'coord@301'"
