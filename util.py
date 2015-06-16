"""
ManyMan - A Many-core Visualization and Management System
Copyright (C) 2012
University of Amsterdam - Computer Systems Architecture
Jimi van der Woning and Roy Bakker

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


def is_prime(n):
    """Determine whether a given number n is a prime number or not."""
    n *= 1.0
    if n % 2 == 0 and n != 2 or n % 3 == 0 and n != 3:
        return False
    for b in range(1, int((n ** 0.5 + 1) / 6.0 + 1)):
        if n % (6 * b - 1) == 0:
            return False
        if n % (6 * b + 1) == 0:
            return False
    return True


def frange(start, stop, step):
    """Float range iterator."""
    eps = 1e-5
    r = start
    while r < stop + eps:
        yield r
        r += step
