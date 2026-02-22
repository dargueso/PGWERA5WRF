"""Tests for pgw4era.utils."""

import datetime as dt

import numpy as np

from pgw4era.utils import calc_midmonth, calc_relhum


class TestCalcMidmonth:
    def test_length(self):
        """calc_midmonth must return exactly 14 elements."""
        result = calc_midmonth(2009)
        assert len(result) == 14

    def test_all_datetimes(self):
        """Every element must be a datetime object."""
        result = calc_midmonth(2009)
        assert all(isinstance(d, dt.datetime) for d in result)

    def test_year_boundary_first_element(self):
        """First element must fall in the previous year (Dec of year-1)."""
        year = 2009
        result = calc_midmonth(year)
        assert result[0].year == year - 1
        assert result[0].month == 12

    def test_year_boundary_last_element(self):
        """Last element must fall in the next year (Jan of year+1)."""
        year = 2009
        result = calc_midmonth(year)
        assert result[-1].year == year + 1
        assert result[-1].month == 1

    def test_inner_months_correct_year(self):
        """Elements [1..12] must all belong to the requested year."""
        year = 2009
        result = calc_midmonth(year)
        for i, element in enumerate(result[1:13], start=1):
            assert element.year == year, f"Element {i} year mismatch: {element}"

    def test_inner_months_sequential(self):
        """Inner 12 elements must be in month-ascending order."""
        result = calc_midmonth(2009)
        inner = result[1:13]
        months = [d.month for d in inner]
        assert months == list(range(1, 13))

    def test_mid_month_is_around_middle(self):
        """Mid-month timestamps must fall on or after the 14th of the month."""
        result = calc_midmonth(2009)
        for element in result[1:13]:
            assert element.day >= 14, f"Expected mid-month >= 14th, got {element}"


class TestCalcRelhum:
    def test_saturated(self):
        """When dew-point equals temperature, RH must be 100%."""
        t = np.array([20.0, 0.0, -10.0])
        rh = calc_relhum(t, t)
        np.testing.assert_allclose(rh, 100.0, atol=1e-6)

    def test_dry_conditions(self):
        """Very low dew-point relative to temperature gives near-zero RH."""
        dewpt = np.array([-40.0])
        t = np.array([30.0])
        rh = calc_relhum(dewpt, t)
        assert rh.item() < 5.0, f"Expected near-zero RH, got {rh.item():.2f}%"

    def test_realistic_values(self):
        """RH from a typical dew-point depression must be in (0, 100)."""
        # 20°C air, 10°C dew-point → approximately 52% RH
        rh = calc_relhum(np.array([10.0]), np.array([20.0]))
        assert 0.0 < rh.item() < 100.0

    def test_output_shape_preserved(self):
        """Output shape must match input shape."""
        dewpt = np.zeros((5, 10))
        t = np.ones((5, 10)) * 15.0
        rh = calc_relhum(dewpt, t)
        assert rh.shape == (5, 10)

    def test_rh_increases_with_dewpt(self):
        """Higher dew-point (closer to T) must give higher RH."""
        t = np.array([20.0])
        rh_low = calc_relhum(np.array([-10.0]), t)
        rh_high = calc_relhum(np.array([15.0]), t)
        assert rh_high.item() > rh_low.item()
