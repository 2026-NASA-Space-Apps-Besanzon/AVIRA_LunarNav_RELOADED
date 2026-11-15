import json
import pytest
from BUILD_NASA_3D_RESULTS import check_source, unit

def test_no_fabricated_nasa_data(tmp_path):
    with pytest.raises(ValueError,match='No NASA evidence manifest'):
        check_source(tmp_path)

def test_synthetic_manifest_rejected(tmp_path):
    (tmp_path/'NASA_DATA_MANIFEST.json').write_text(json.dumps({'status':'SYNTHETIC','sites':{'a':{},'b':{}}}))
    with pytest.raises(ValueError,match='LIVE NASA'):
        check_source(tmp_path)

def test_direction_convention():
    assert unit(90,0)[0] == pytest.approx(1)
    assert unit(0,90)[2] == pytest.approx(1)
