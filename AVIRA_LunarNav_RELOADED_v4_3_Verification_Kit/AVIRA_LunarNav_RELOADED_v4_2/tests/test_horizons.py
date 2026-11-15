from datetime import date
from unittest.mock import patch
import pytest
from horizons import get_observer_ephemeris,HorizonsError

class Response:
    def __init__(self,body):self.body=body
    def raise_for_status(self):pass
    def json(self):return {'result':self.body}

def fake_reply(start=True,end=True):
    lines=[]
    if start: lines.append('2026-Nov-15 00:00, , 45.0, +4.0,')
    lines.append('2026-Nov-15 12:00, , 46.0, -2.5,')
    if end: lines.append('2026-Nov-16 00:00, , 48.0, -3.0,')
    return 'Header\n$$SOE\n'+'\n'.join(lines)+'\n$$EOE\n'

def test_jpl_csv_smoke_mock():
    with patch('horizons.requests.get',return_value=Response(fake_reply())) as req:
        p=get_observer_ephemeris('10',-89,15,date(2026,11,15),days=1,step='12h')
        assert len(p)==3 and p[1]['el']==-2.5
        args=req.call_args.kwargs['params']
        assert args['CENTER']=="'coord@301'" and args['QUANTITIES']=="'4'"

def test_horizons_incomplete_coverage_fails_closed():
    with patch('horizons.requests.get',return_value=Response(fake_reply(end=False))):
        with pytest.raises(HorizonsError,match='coverage incomplete'):
            get_observer_ephemeris('10',-89,15,date(2026,11,15),days=1,step='12h')

def test_horizons_missing_table_fails_closed():
    with patch('horizons.requests.get',return_value=Response('No matching ephemeris')):
        with pytest.raises(HorizonsError,match='did not return'):
            get_observer_ephemeris('10',-89,15,date(2026,11,15),days=1)
