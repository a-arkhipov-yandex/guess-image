from __future__ import annotations

import pytest

from guess_image_lib import *

def testPrepare():
    initLog()
    assert(True)

@pytest.mark.parametrize(
    "i, expected_result",
    [
        ('1983', 1983), # Good int
        ('1980е', False), # Incorrect int
        ('i1980', False), # Incorrect int
        ('1$980', False), # Incorrect int
    ],
)
def testMyInt(i, expected_result):
    ret = myInt(i)
    assert(ret == expected_result)

# Test user name format
@pytest.mark.parametrize(
    "p, expected_result",
    [
        ('123dfdf', False),
        ('dfввв12', False),
        ('s232', True),
        ('s232f', True),
        ('s23#2', False),
        ('s/232', False),
        ('s#232', False),
        ('s$232', False),
        ('s%232', False),
        ('s2.32', False),
        ('alex-arkhipov', True),
        ('alex_arkhipov', True),
    ],
)
def testCheckUserNameFormat(p, expected_result):
    ret = checkUserNameFormat(p)
    assert(ret == expected_result)

@pytest.mark.parametrize(
    "year, expected_result",
    [
        ('1983 г', '1983'), # Good one year
        ('1980е г', '1980е'), # Good one year with 'e'
        ('ок 1985 г', '1985'), # Good OK at the beggining
        ('1987', None), # No 'г.' at the end
        ('ок 1988', None), # No 'г.' at the end with 'ок.'
        ('ок 1983-1989 г', '1983-1989'), # Good ok and 'г.'
        ('1985-1987 г', '1985-1987'), # Good 'г.' - range
        ('1 г', None), # Len < 4
        ('12г', None), # Len < 4 no space
    ],
)
def testRemoveYearSigns(year, expected_result):
    ret = removeYearSigns(year)
    assert(ret == expected_result)

@pytest.mark.parametrize(
    "year, expected_result",
    [
        ('1983 г', 1983), # Good one year
        ('1980е г', 1980), # Good one year with 'e'
        ('983 г', 0), # Too small one year
        ('3983 г', 0), # Too big one year
        ('ок 1985 г', 1985), # Good OK at the beggining
        ('1987', False), # No 'г.' at the end
        ('ок 1988', False), # No 'г.' at the end with 'ок.'
        ('ок 1983-1989 г', 1986), # Good ok and 'г.'
        ('1985-1987 г', 1986), # Good 'г.' - range
        ('1 г', False), # Len < 4
        ('12г', False), # Len < 4 no space
    ],
)
def testGetYear(year, expected_result):
    ret = getYear(year)
    assert(ret == expected_result)

def testCleanup():
    closeLog()
    assert(True)
