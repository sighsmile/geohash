#!/usr/bin/env python
# -*- coding: utf-8 -*-

# author:    sighsmile.github.io
# date:   2017-06-30

import itertools
import math

BASE32 = '0123456789bcdefghjkmnpqrstuvwxyz'  # 0-9 and b-z
CHARMAP = {c: i for i, c in enumerate(BASE32)}


def _char2bits(c):
    """
    convert char c from base32 to 5-bit-string
    this is slower than bit operations
    and is only meant to demonstrate the algorithm
    """
    return "{0:05b}".format(CHARMAP[c])


def _geohash2bits(geohash):
    """
    decode from base32 using CHARMAP
    return a bits string
    """
    bits = ''.join([_char2bits(c) for c in geohash])
    return bits


def _bits2coordinate(bits, lo, hi):
    """
    decode bits (iteratable) into coordinate value and error
    """
    for b in bits:
        mid = (lo + hi) / 2
        if b == '1':
            lo = mid
        else:
            hi = mid

    return (lo + hi) / 2, (hi - lo) / 2


def _get_precision(err):
    """
    return number of siginificant digits after decimal mark
    final rounding should ensure that
        val - err <= round(val) <= val + err
    e.g. if val = 42.605, err = 0.022, round(val) should be 42.61 or 42.60
    if val = 42.627, err = 0.088, round(val) should be 42.6 but not 42

    notice that lng_err is always either lat_err or twice lat_err
    so using lng_err to get precision is sufficient
    """
    return max(0, int(-math.log10(2 * err)) + 1)


def _decode_val_err(geohash):
    """
    decode geohash string to coordinates and errors
    return loggitude value, latitude value, longitude error, latitude error
    this uses string conversions which are slower than bit operations
    and is only meant to demonstrate the algorithm
    """
    bits = _geohash2bits(geohash)
    lat_bits = itertools.islice(bits, 1, None, 2)
    lat_val, lat_err = _bits2coordinate(lat_bits, -90, 90)
    lng_bits = itertools.islice(bits, 0, None, 2)
    lng_val, lng_err = _bits2coordinate(lng_bits, -180, 180)
    return lat_val, lng_val, lat_err, lng_err


def _decode(geohash):
    """
    decode geohash string to coordinate strings
    properly rounded, may have ending zeros
    """
    lat_val, lng_val, lat_err, lng_err = _decode_val_err(geohash)
    precision = _get_precision(lng_err)
    lat_val = "%.*f" % (precision, lat_val)
    lng_val = "%.*f" % (precision, lng_val)
    return lat_val, lng_val


def decode_val_err(geohash):
    """
    decode geohash string to coordinates and errors
    return loggitude value, latitude value, longitude error, latitude error
    this uses bit operations
    """

    lat_lo, lat_hi = -90, 90
    lng_lo, lng_hi = -180, 180
    is_lng = True
    masks = [16, 8, 4, 2, 1]  # use bit operation to make base32 convert fast

    for c in geohash:
        d = CHARMAP[c]
        for mask in masks:
            if is_lng:
                mid = (lng_lo + lng_hi) / 2
                if d & mask:
                    lng_lo = mid
                else:
                    lng_hi = mid
            else:
                mid = (lat_lo + lat_hi) / 2
                if d & mask:
                    lat_lo = mid
                else:
                    lat_hi = mid
            is_lng = not is_lng

    lat_val = (lat_lo + lat_hi) / 2
    lng_val = (lng_lo + lng_hi) / 2
    lat_err = (lat_hi - lat_lo) / 2
    lng_err = (lng_hi - lng_lo) / 2

    return lat_val, lng_val, lat_err, lng_err


def decode(geohash):
    """
    decode geohash string to coordinate strings
    properly rounded, may have ending zeros
    """
    try:
        lat_val, lng_val, lat_err, lng_err = decode_val_err(geohash)
        precision = _get_precision(lng_err)
        lat_val = "%.*f" % (precision, lat_val)
        lng_val = "%.*f" % (precision, lng_val)
        return lat_val, lng_val
    except:
        print("Unable to decode!")  # TODO better error message


def _coordinate2bits(val, lo, hi, length):
    """
    encode one coordinate to bits-string of desired length
    """
    bits = ''
    while len(bits) < length:
        mid = (lo + hi) / 2
        if val > mid:
            bits += '1'
            lo = mid
        else:
            bits += '0'
            hi = mid
    return bits


def _encode(lat_val, lng_val, length=12):
    """
    encode latitude, longitude coordinates into geohash
    return geohash string with desired length
    """
    lat_bits = _coordinate2bits(lat_val, -90, 90, length * 5 // 2)
    lng_bits = _coordinate2bits(lng_val, -180, 180, (length * 5 + 1) // 2)
    bits = ''.join(itertools.chain.from_iterable(
                itertools.zip_longest(lng_bits, lat_bits, fillvalue='')))
    numbers = [int(bits[i:i+5], 2) for i in range(0, len(bits), 5)]
    hashstr = ''.join(BASE32[i] for i in numbers)
    return hashstr


# TODO: could implement a wrapper like decode()
def encode(lat_val, lng_val, length=12):
    """
    encode latitude, longitude coordinates into geohash
    return geohash string with desired length
    """
    hashstr = ''
    lat_lo, lat_hi = -90, 90
    lng_lo, lng_hi = -180, 180
    is_lng = True
    masks = [16, 8, 4, 2, 1]  # use bit operation to make base32 convert fast

    d = 0
    bit = 0
    while len(hashstr) < length:
        if is_lng:
            mid = (lng_lo + lng_hi) / 2
            if lng_val > mid:
                d |= masks[bit]
                lng_lo = mid
            else:
                lng_hi = mid
        else:
            mid = (lat_lo + lat_hi) / 2
            if lat_val > mid:
                d |= masks[bit]
                lat_lo = mid
            else:
                lat_hi = mid

        is_lng = not is_lng
        if bit < 4:
            bit += 1
        else:
            hashstr += BASE32[d]
            bit = 0
            d = 0
    return hashstr
