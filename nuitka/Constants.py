#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Module for constants in Nuitka.

This contains means to compare, classify and test constants.
"""

import math

# pylint: disable=W0622
from .__past__ import long, unicode, iterItems
# pylint: enable=W0622

from .Builtins import builtin_anon_names
from .Utils import python_version

NoneType = type( None )

def compareConstants( a, b ):
    # Many many cases to deal with, pylint: disable=R0911,R0912

    # Supposed fast path for comparison.
    if type( a ) is not type( b ):
        return False

    # Now it's either not the same, or it is a container that contains NaN or it is a
    # complex or float that is NaN, the other cases can use == at the end.
    if type( a ) is complex:
        return compareConstants( a.imag, b.imag ) and compareConstants( a.real, b.real )

    if type( a ) is float:
        # Check sign first, -0.0 is not 0.0, or -nan is not nan, it has a different sign
        # for a start.
        if math.copysign( 1.0, a ) != math.copysign( 1.0, b ):
            return False

        if math.isnan( a ) and math.isnan( b ):
            return True

        return a == b

    if type( a ) in ( tuple, list ):
        if len( a ) != len( b ):
            return False

        for ea, eb in zip( a, b ):
            if not compareConstants( ea, eb ):
                return False
        else:
            return True

    if type( a ) is dict:
        if len( a ) != len( b ):
            return False

        for ea1, ea2 in iterItems( a ):
            for eb1, eb2 in iterItems( b ):
                if compareConstants( ea1, eb1 ) and compareConstants( ea2, eb2 ):
                    break
            else:
                return False
        else:
            return True

    if type( a ) in ( frozenset, set ):
        if len( a ) != len( b ):
            return False

        for ea in a:
            if ea not in b:
                # Due to NaN values, we need to compare each set element with all the
                # other set to be really sure.
                for eb in b:
                    if compareConstants( ea, eb ):
                        break
                else:
                    return False
        else:
            return True

    if type( a ) is range:
        return str( a ) == str( b )

    # The NaN values of float and complex may let this fail, even if the constants are
    # built in the same way.
    return a == b

# These builtin type references are kind of constant too. TODO: The list is
# totally not complete.
constant_builtin_types = int, set, str, float, list, tuple, dict, complex

if python_version >= 300:
    constant_builtin_types += (
        range,
        bytes,
    )
else:
    constant_builtin_types += (
        unicode,
        long,
        # This has no name in Python, but the natural one in C-API.
        builtin_anon_names[ "instance" ]
    )

def isConstant( constant ):
    # Too many cases and all return, that is how we do it here,
    # pylint: disable=R0911,R0912

    constant_type = type( constant )

    if constant_type is dict:
        for key, value in iterItems( constant ):
            if not isConstant( key ):
                return False
            if not isConstant( value ):
                return False
        else:
            return True
    elif constant_type in ( tuple, list ):
        for element_value in constant:
            if not isConstant( element_value ):
                return False
        else:
            return True
    elif constant_type in ( str, unicode, complex, int, long, bool, float, NoneType,
                            range, bytes, set ):
        return True
    elif constant in ( Ellipsis, NoneType ):
        return True
    elif constant_type is type:
        return constant in constant_builtin_types
    else:
        return False


def isMutable( constant ):
    constant_type = type( constant )

    if constant_type in ( str, unicode, complex, int, long, bool, float, NoneType, range, bytes ):
        return False
    elif constant_type in ( dict, list, set ):
        return True
    elif constant_type is tuple:
        for value in constant:
            if isMutable( value ):
                return True
        else:
            return False
    elif constant is Ellipsis:
        # Note: Workaround for Ellipsis not being handled by the pickle module,
        # pretend it would be mutable, then it doesn't get pickled as part of lists or
        # tuples. This is a loss of efficiency, but usage of Ellipsis will be very
        # limited normally anyway.
        return True
    else:
        assert False, constant_type

def isIterableConstant( constant ):
    return type( constant ) in ( str, unicode, list, tuple, set, frozenset, dict, range, bytes )

def getConstantIterationLength( constant ):
    assert isIterableConstant( constant )

    return len( constant )

def isNumberConstant( constant ):
    return type( constant ) in ( int, long, float, bool )

def isIndexConstant( constant ):
    return type( constant ) in ( int, long, bool )

class HashableConstant:
    def __init__( self, constant ):
        self.constant = constant

        try:
            # For Python3: range objects with same ranges give different hash
            # values. It's not even funny, is it.
            if type( constant ) is range:
                raise TypeError

            self.hash = hash( constant )
        except TypeError:
            self.hash = 55

    def getConstant( self ):
        return self.constant

    def __hash__( self ):
        return self.hash

    def __eq__( self, other ):
        assert isinstance( other, self.__class__ )

        return compareConstants( self.constant, other.constant )
