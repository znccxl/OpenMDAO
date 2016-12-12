"""
Classes and functions to support unit conversion.

The module provides a basic set of predefined physical quantities
in its built-in library; however, it also supports generation of
personal libararies which can be saved and reused.
This module is based on the PhysicalQuantities module
in Scientific Python, by Konrad Hinsen. Modifications by
Justin Gray.
"""

from __future__ import division, print_function


import re
import os.path
from collections import OrderedDict
from six import iteritems
from six.moves.configparser import RawConfigParser as ConfigParser

# pylint: disable=E0611, F0401
from math import sin, cos, tan, floor, pi


####################################
# Class Definitions
####################################


class NumberDict(OrderedDict):
    """Dictionary storing numerical values.

    An instance of this class acts like an array of numbers with
    generalized (non-integer) indices. A value of zero is assumed
    for undefined entries. NumberDict instances support addition
    and subtraction with other NumberDict instances, and multiplication
    and division by scalars.
    """

    def __getitem__(self, item):
        """
        get the item, or 0.

        Args
        ----
        item : key
            key to get the item

        Returns
        -------
        int
            value of the given key
        """
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            return 0

    def __coerce__(self, other):
        """
        change other dict to NumberDicts.

        Args
        ----
        other : Dict
            the dict instance to be coerced

        Returns
        -------
        NumberDict
            new NumberDict with keys/values from original
        """
        if isinstance(other, dict):
            other = NumberDict(other)
        return self, other

    def __add__(self, other):
        """
        add another NumberDict to myself.

        Args
        ----
        other : NumberDict
            the other NumberDict Instance

        Returns
        -------
        NumberDict
            new NumberDict with self+other values
        """
        sum_dict = NumberDict()
        for k, v in iteritems(self):
            sum_dict[k] = v
        for k, v in iteritems(other):
            sum_dict[k] = sum_dict[k] + v
        return sum_dict

    def __sub__(self, other):
        """
        add another NumberDict from myself.

        Args
        ----
        other : NumberDict
            the other NumberDict Instance

        Returns
        -------
        NumberDict
            new NumberDict instance, with self-other values
        """
        sum_dict = NumberDict()
        for k, v in iteritems(self):
            sum_dict[k] = v
        for k, v in iteritems(other):
            sum_dict[k] = sum_dict[k] - v
        return sum_dict

    def __rsub__(self, other):
        """
        add subtract myself from another NumberDict.

        Args
        ----
        other : NumberDict
            the other NumberDict Instance

        Returns
        -------
        NumberDict
            new NumberDict instance, with other-self values
        """
        sum_dict = NumberDict()
        for k, v in iteritems(other):
            sum_dict[k] = v
        for k, v in iteritems(self):
            sum_dict[k] = sum_dict[k] - v
        return sum_dict

    def __mul__(self, other):
        """
        multiply myself by another NumberDict.

        Args
        ----
        other : NumberDict
            the other NumberDict Instance

        Returns
        -------
        NumberDict
            new NumberDict instance, with other*self values
        """
        new = NumberDict()
        for key, value in iteritems(self):
            new[key] = other * value
        return new

    __rmul__ = __mul__

    def __div__(self, other):
        """
        divide myself by another NumberDict.

        Args
        ----
        other : int
            value to divide by

        Returns
        -------
        NumberDict
            new NumberDict instance, with self/other values
        """
        new = NumberDict()
        for key, value in iteritems(self):
            new[key] = value / other
        return new

    __truediv__ = __div__  # for python 3

    def __repr__(self):
        """
        Return a string deceleration of myself.

        Args
        ----
        other : NumberDict
            the other NumberDict Instance

        Returns
        -------
        str
            str representation for the creation of this NumberDict
        """
        return repr(dict(self))


class PhysicalUnit(object):
    """Physical unit.

    A physical unit is defined by a name (possibly composite), a scaling
    factor, and the exponentials of each of the SI base units that enter into
    it. Units can be multiplied, divided, and raised to integer powers.

    Attributes
    ----------
    _names : dict or str
        A dictionary mapping each name component to its
        associated integer power (e.g., C{{'m': 1, 's': -1}})
        for M{m/s}). As a shorthand, a string may be passed
        which is assigned an implicit power 1.
    _factor : float
        A scaling factor.
    _powers : list of int
        The integer powers for each of the nine base units.
    _offset : float
        An additive offset to the base unit (used only for temperatures)
    """

    def __init__(self, names, factor, powers, offset=0):
        """Initialize all attributes.

        Args
        ----
        names : dict or str
            A dictionary mapping each name component to its
            associated integer power (e.g., C{{'m': 1, 's': -1}})
            for M{m/s}). As a shorthand, a string may be passed
            which is assigned an implicit power 1.
        factor : float
            A scaling factor.
        powers : list of int
            The integer powers for each of the nine base units.
        offset : float
            An additive offset to the base unit (used only for temperatures).
        """
        if isinstance(names, str):
            self._names = NumberDict(((names, 1),))
        else:
            self._names = names

        self._factor = float(factor)
        self._offset = float(offset)
        self._powers = powers

    def __repr__(self):
        """string representation of myself.

        Returns
        -------
        str
            str representation of how to instantiate this PhysicalUnit
        """
        return 'PhysicalUnit(%s,%s,%s,%s)' % (self._names, self._factor,
                                              self._powers, self._offset)

    def __str__(self):
        """convert myself to string.

        Returns
        -------
        str
            str representation of a PhysicalUnit
        """
        return '<PhysicalUnit ' + self.name() + '>'

    def __lt__(self, other):
        """compare myself to other.

        Args
        ----
        other : PhysicalUnit
            The other physical unit to be compared to

        Returns
        -------
        bool
            self._factor < other._factor
        """
        if self._powers != other._powers or self._offset != other._offset:
            raise TypeError('Incompatible units')

        return self._factor < other._factor

    def __gt__(self, other):
        """compare myself to other.

        Args
        ----
        other : PhysicalUnit
            The other physical unit to be compared to

        Returns
        -------
        bool
            self._factor > other._factor
        """
        if self._powers != other._powers:
            raise TypeError('Incompatible units')
        return self._factor > other._factor

    def __eq__(self, other):
        """test for equality.

        Args
        ----
        other : PhysicalUnit
            The other physical unit to be compared to

        Returns
        -------
        bool
            true if _factor, _offset, and _powers all match
        """
        return (self._factor == other._factor and
                self._offset == other._offset and
                self._powers == other._powers)

    def __mul__(self, other):
        """multiply myself by other.

        Args
        ----
        other : PhysicalUnit
            The other physical unit to be compared to

        Returns
        -------
        PhysicalUnit
            new PhysicalUnit instance representing the product of two units
        """
        if self._offset != 0 or (isinstance(other, PhysicalUnit) and
                                 other._offset != 0):
            raise TypeError("cannot multiply units with non-zero offset")
        if isinstance(other, PhysicalUnit):
            return PhysicalUnit(self._names + other._names,
                                self._factor * other._factor,
                                [a + b for (a, b) in zip(self._powers,
                                                         other._powers)])
        else:
            return PhysicalUnit(self._names + {str(other): 1},
                                self._factor * other,
                                self._powers,
                                self._offset * other)

    __rmul__ = __mul__

    def __div__(self, other):
        """divide myself by other.

        Args
        ----
        other : PhysicalUnit
            The other physical unit to be operated on

        Returns
        -------
        PhysicalUnit
            new PhysicalUnit instance representing the self/other
        """
        if self._offset != 0 or (isinstance(other, PhysicalUnit) and
                                 other._offset != 0):
            raise TypeError("cannot divide units with non-zero offset")
        if isinstance(other, PhysicalUnit):
            return PhysicalUnit(self._names - other._names,
                                self._factor / other._factor,
                                [a - b for (a, b) in zip(self._powers,
                                                         other._powers)])
        else:
            return PhysicalUnit(self._names + {str(other): -1},
                                self._factor / float(other), self._powers)

    __truediv__ = __div__   # for python 3

    def __rdiv__(self, other):
        """divide other by myself.

        Args
        ----
        other : PhysicalUnit
            The other physical unit to be operated on

        Returns
        -------
        PhysicalUnit
            new PhysicalUnit instance representing the other/self
        """
        return PhysicalUnit({str(other): 1} - self._names,
                            float(other) / self._factor,
                            [-x for x in self._powers])

    __rtruediv__ = __rdiv__

    def __pow__(self, other):
        """raise myself to a power.

        Args
        ----
        other : float or int
            power to raise self by

        Returns
        -------
        PhysicalUnit
            new PhysicalUnit of self^other
        """
        if self._offset != 0:
            raise TypeError("cannot exponentiate units with non-zero offset")
        if isinstance(other, int):
            return PhysicalUnit(other * self._names, pow(self._factor, other),
                                [x * other for x in self._powers])
        if isinstance(other, float):
            inv_exp = 1. / other
            rounded = int(floor(inv_exp + 0.5))
            if abs(inv_exp - rounded) < 1.e-10:

                if all([x % rounded == 0 for x in self._powers]):
                    f = self._factor**other
                    p = [x / rounded for x in self._powers]
                    if all([x % rounded == 0 for x in self._names.values()]):
                        names = self._names / rounded
                    else:
                        names = NumberDict()
                        if f != 1.:
                            names[str(f)] = 1
                        for x, name in zip(p, _UNIT_LIB.base_names):
                            names[name] = x
                    return PhysicalUnit(names, f, p)

        raise TypeError('Only integer and inverse integer exponents allowed')

    def in_base_units(self):
        """
        Return the base unit equivalent of this unit.

        Returns
        -------
        PhysicalUnit
            the equivalent base unit
        """
        num = ''
        denom = ''
        for unit, power in zip(_UNIT_LIB.base_names, self._powers):
            if power < 0:
                denom = denom + '/' + unit
                if power < -1:
                    denom = denom + '**' + str(-power)
            elif power > 0:
                num = num + '*' + unit
                if power > 1:
                    num = num + '**' + str(power)

        if len(num) == 0:
            num = '1'
        else:
            num = num[1:]

        return _find_unit(num + denom)

    def conversion_tuple_to(self, other):
        """Compute the tuple of (factor, offset) for conversion.

        Args
        ----
        other : PhysicalUnit
            Another unit.

        Returns
        -------
        Tuple with two floats
            The conversion factor and offset from this unit to another unit.
        """
        if self._powers != other._powers:
            raise TypeError('Incompatible units')

        # let (s1,d1) be the conversion tuple from 'self' to base units
        #   (ie. (x+d1)*s1 converts a value x from 'self' to base units,
        #   and (x/s1)-d1 converts x from base to 'self' units)
        # and (s2,d2) be the conversion tuple from 'other' to base units
        # then we want to compute the conversion tuple (S,D) from
        #   'self' to 'other' such that (x+D)*S converts x from 'self'
        #   units to 'other' units
        # the formula to convert x from 'self' to 'other' units via the
        #   base units is (by definition of the conversion tuples):
        #     ( ((x+d1)*s1) / s2 ) - d2
        #   = ( (x+d1) * s1/s2) - d2
        #   = ( (x+d1) * s1/s2 ) - (d2*s2/s1) * s1/s2
        #   = ( (x+d1) - (d1*s2/s1) ) * s1/s2
        #   = (x + d1 - d2*s2/s1) * s1/s2
        # thus, D = d1 - d2*s2/s1 and S = s1/s2

        factor = self._factor / other._factor
        offset = self._offset - (other._offset * other._factor / self._factor)
        return (factor, offset)

    def is_compatible(self, other):
        """
        check for compatibility with another unit.

        Args
        ----
        other : PhysicalUnit
            Another unit.

        Returns
        -------
        bool
            indicates if two units are compatible
        """
        return self._powers == other._powers

    def is_dimensionless(self):
        """Dimensionless PQ.

        Returns
        -------
        bool
            indicates if this is dimensionless
        """
        return not any(self._powers)

    def is_angle(self):
        """Check if this PQ is an Angle.

        Returns
        -------
        bool
            indicates if this an angle type
        """
        return (self._powers[_UNIT_LIB.base_types['angle']] == 1 and
                sum(self._powers) == 1)

    def set_name(self, name):
        """Set the name.

        Args
        ----
        name : str
            the name
        """
        self._names = NumberDict()
        self._names[name] = 1

    def name(self):
        """compute the name of this unit.

        Returns
        -------
        str
            str representation of the unit
        """
        num = ''
        denom = ''
        for unit, power in iteritems(self._names):
            if power < 0:
                denom = denom + '/' + unit
                if power < -1:
                    denom = denom + '**' + str(-power)
            elif power > 0:
                num = num + '*' + unit
                if power > 1:
                    num = num + '**' + str(power)
        if len(num) == 0:
            num = '1'
        else:
            num = num[1:]
        return num + denom


####################################
# Module Functions
####################################

def _new_unit(name, factor, powers):
    """Create new Unit.

    Args
    ----
    factor : float
        conversion factor to base units
    powers : [int, ...]
        power of base units

    """
    _UNIT_LIB.unit_table[name] = PhysicalUnit(name, factor, powers)


def add_offset_unit(name, baseunit, factor, offset, comment=''):
    """Adding Offset Unit.

    Args
    ----
    unit : str
        newly defined unit
    offset : float
        zero offset for new unit
    comment : str
        optional comment to describe unit
    """
    if isinstance(baseunit, str):
        baseunit = _find_unit(baseunit)
    # else, baseunit should be a instance of PhysicalUnit
    # names, factor, powers, offset=0
    unit = PhysicalUnit(baseunit._names, baseunit._factor * factor,
                        baseunit._powers, offset)
    unit.set_name(name)
    if name in _UNIT_LIB.unit_table:
        if (_UNIT_LIB.unit_table[name]._factor != unit._factor or
                _UNIT_LIB.unit_table[name]._powers != unit._powers):
            raise KeyError("Unit %s already defined with " % name +
                           "different factor or powers")
    _UNIT_LIB.unit_table[name] = unit
    _UNIT_LIB.set('units', name, unit)
    if comment:
        _UNIT_LIB.help.append((name, comment, unit))


def add_unit(name, unit, comment=''):
    """Adding Unit.

    Args
    ----
    unit : str
        newly defined unit
    comment : str
        optional comment to describe unit
    """
    if comment:
        _UNIT_LIB.help.append((name, comment, unit))
    if isinstance(unit, str):
        unit = eval(unit, {'__builtins__': None, 'pi': pi},
                    _UNIT_LIB.unit_table)
    unit.set_name(name)
    if name in _UNIT_LIB.unit_table:
        if (_UNIT_LIB.unit_table[name]._factor != unit._factor or
                _UNIT_LIB.unit_table[name]._powers != unit._powers):
            raise KeyError("Unit %s already defined with " % name +
                           "different factor or powers")

    _UNIT_LIB.unit_table[name] = unit
    _UNIT_LIB.set('units', name, unit)


_UNIT_LIB = ConfigParser()


def _do_nothing(string):
    """Make the ConfigParser case sensitive."""
    return string


_UNIT_LIB.optionxform = _do_nothing


def import_library(libfilepointer):
    """Import a units library, replacing any existing definitions.

    Args
    ----
    libfilepointer : file
        new library file to work with

    Returns
    -------
    ConfigParser
        newly updated units library for the module
    """
    global _UNIT_LIB
    global _UNIT_CACHE
    _UNIT_CACHE = {}
    _UNIT_LIB = ConfigParser()
    _UNIT_LIB.optionxform = _do_nothing
    _UNIT_LIB.readfp(libfilepointer)
    required_base_types = ['length', 'mass', 'time', 'temperature', 'angle']
    _UNIT_LIB.base_names = list()
    # used to is_angle() and other base type checking
    _UNIT_LIB.base_types = dict()
    _UNIT_LIB.unit_table = dict()
    _UNIT_LIB.prefixes = dict()
    _UNIT_LIB.help = list()

    for prefix, factor in _UNIT_LIB.items('prefixes'):
        factor, comma, comment = factor.partition(',')
        _UNIT_LIB.prefixes[prefix] = float(factor)

    base_list = [0] * len(_UNIT_LIB.items('base_units'))

    for i, (unit_type, name) in enumerate(_UNIT_LIB.items('base_units')):
        _UNIT_LIB.base_types[unit_type] = i
        powers = list(base_list)
        powers[i] = 1
        # print '%20s'%unit_type, powers
        # cant use add_unit because no base units exist yet
        _new_unit(name, 1, powers)
        _UNIT_LIB.base_names.append(name)

    # test for required base types
    missing = [utype for utype in required_base_types
               if utype not in _UNIT_LIB.base_types]
    if missing:
        raise ValueError('Not all required base type were present in the'
                         ' config file. missing: %s, at least %s required'
                         % (missing, required_base_types))

    # Explicit unitless 'unit'.
    _new_unit('unitless', 1, list(base_list))
    _update_library(_UNIT_LIB)
    return _UNIT_LIB


def update_library(filename):
    """
    Update units in current library from `filename`.

    Args
    ----
    filename: string or file
        Source of units configuration data.
    """
    if isinstance(filename, basestring):
        inp = open(filename, 'rU')
    else:
        inp = filename
    try:
        cfg = ConfigParser()
        cfg.optionxform = _do_nothing
        cfg.readfp(inp)
        _update_library(cfg)
    finally:
        inp.close()


def _update_library(cfg):
    """Update library from :class:`ConfigParser` `cfg`.

    Args
    ----
    cfg: ConfigParser
        ConfigParser loaded with unit_lib.ini data
    """
    retry1 = set()
    for name, unit in cfg.items('units'):
        data = [item.strip() for item in unit.split(',')]
        if len(data) == 2:
            unit, comment = data
            try:
                add_unit(name, unit, comment)
            except NameError:
                retry1.add((name, unit, comment))
        elif len(data) == 4:
            factor, baseunit, offset, comment = data
            try:
                add_offset_unit(name, baseunit, float(factor), float(offset),
                                comment)
            except NameError:
                retry1.add((name, baseunit, float(factor), float(offset),
                            comment))
        else:
            raise ValueError('Unit %r definition %r has invalid format',
                             name, unit)
    retry_count = 0
    last_retry_count = -1
    while last_retry_count != retry_count and retry1:
        last_retry_count = retry_count
        retry_count = 0
        retry2 = retry1.copy()
        for data in retry2:
            if len(data) == 3:
                name, unit, comment = data
                try:
                    add_unit(name, unit, comment)
                    retry1.remove(data)
                except NameError:
                    retry_count += 1
            else:
                try:
                    name, factor, baseunit, offset, comment = data
                    add_offset_unit(name, factor, baseunit, offset, comment)
                    retry1.remove(data)
                except NameError:
                    retry_count += 1
    if retry1:
        raise ValueError('The following units were not defined because they'
                         ' could not be resolved as a function of any other'
                         ' defined units:%s' % [x[0] for x in retry1])


_UNIT_CACHE = {}


def _find_unit(unit):
    """Find unit helper function.

    Args
    ----
    unit: str
        str representing the desired unit

    Returns
    -------
    PhysicalUnit
        The actual unit object
    """
    if isinstance(unit, str):
        name = unit.strip()
        try:
            unit = _UNIT_CACHE[name]
        except KeyError:
            try:
                unit = eval(name, {'__builtins__': None}, _UNIT_LIB.unit_table)
            except Exception:

                # This unit might include prefixed units that aren't in the
                # unit_table. We must parse them ALL and add them to the
                # unit_table.

                # First character of a unit is always alphabet or $.
                # Remaining characters may include numbers.
                regex = re.compile('[A-Z,a-z]{1}[A-Z,a-z,0-9]*')

                for item in regex.findall(name):
                    # check if this was a compound unit, so each
                    # substring might be a unit
                    try:
                        eval(item, {'__builtins__': None},
                             _UNIT_LIB.unit_table)
                    except Exception:  # maybe is a prefixed unit then
                        # check for single letter prefix before unit
                        if(item[0] in _UNIT_LIB.prefixes and
                           item[1:] in _UNIT_LIB.unit_table):
                            add_unit(item, _UNIT_LIB.prefixes[item[0]] *
                                     _UNIT_LIB.unit_table[item[1:]])

                        # check for double letter prefix before unit
                        elif(item[0:2] in _UNIT_LIB.prefixes and
                             item[2:] in _UNIT_LIB.unit_table):
                            add_unit(item, _UNIT_LIB.prefixes[item[0:2]] *
                                     _UNIT_LIB.unit_table[item[2:]])

                        # no prefixes found, unknown unit
                        else:
                            raise ValueError("no unit named '%s' is defined"
                                             % item)

                unit = eval(name, {'__builtins__': None}, _UNIT_LIB.unit_table)

            _UNIT_CACHE[name] = unit

    if not isinstance(unit, PhysicalUnit):
        raise TypeError(str(unit) + ' is not a unit')
    return unit


def conversion_to_base_units(units):
    """
    Get the offset and scaler to convert from given units to base units.

    Args
    ----
    units : str
        String representation of the units.

    Returns
    -------
    float
        Offset to get to default unit: m (length), s(time), etc.
    float
        Mult. factor to get to default unit: m (length), s(time), etc.
    """
    if not units:  # dimensionless
        return 0., 1.
    unit = _find_unit(units)

    return unit._offset, unit._factor


def is_compatible(old_units, new_units):
    """Check whether units are compatible in terms of base units.

    e.g., m/s is compatible with ft/hr

    Args
    ----
    old_units : str
        original units as a string.
    new_units : str or None
        new units to return the value in; if None, return in standard units.

    Returns
    -------
    bool
        whether the units are compatible.
    """
    if not old_units and not new_units:  # dimensionless
        return True

    old_unit = _find_unit(old_units)
    new_unit = _find_unit(new_units)

    return old_unit.is_compatible(new_unit)


def convert_units(val, old_units, new_units=''):
    """Take a given quantity and return in different units.

    Args
    ----
    val : float
        value in original units.
    old_units : str
        original units as a string.
    new_units : str
        new units to return the value in; if empty str,
        return in standard units.

    Returns
    -------
    float
        value in new units.
    """
    if not old_units and not new_units:  # dimensionless
        return val

    old_unit = _find_unit(old_units)
    if new_units:
        new_unit = _find_unit(new_units)
    else:
        new_unit = old_unit.in_base_units()

    (factor, offset) = old_unit.conversion_tuple_to(new_unit)
    return (val + offset) * factor


# Load in the default unit library
file_path = open(os.path.join(os.path.dirname(__file__),
                 'unit_library.ini'))
with file_path as default_lib:
    import_library(default_lib)


if __name__ == '__main__':
    for returned, expected in [
        (conversion_to_base_units('cm'), (0., 1.0e-2)),
        (conversion_to_base_units('km'), (0., 1.0e3)),
        (convert_units(3.0, 'mm'), (3.0e-3)),
        (convert_units(3.0, 'mm', 'cm'), (3.0e-1))
    ]:
        print(returned, 'should be', expected)
