# -*- coding: utf-8 -*-
#
# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from mycroft.util.lang.format_common import convert_to_mixed_fraction
from mycroft.util.log import LOG
from mycroft.util.lang.common_data_en import _NUM_STRING_EN, \
    _FRACTION_STRING_EN, _LONG_SCALE_EN, _SHORT_SCALE_EN


def nice_number_en(number, speech, denominators):
    """ English helper for nice_number

    This function formats a float to human understandable functions. Like
    4.5 becomes "4 and a half" for speech and "4 1/2" for text

    Args:
        number (int or float): the float to format
        speech (bool): format for speech (True) or display (False)
        denominators (iter of ints): denominators to use, default [1 .. 20]
    Returns:
        (str): The formatted string.
    """

    result = convert_to_mixed_fraction(number, denominators)
    if not result:
        # Give up, just represent as a 3 decimal number
        return str(round(number, 3))

    whole, num, den = result

    if not speech:
        return str(whole) if num == 0 else f'{whole} {num}/{den}'
    if num == 0:
        return str(whole)
    den_str = _FRACTION_STRING_EN[den]
    if whole == 0:
        return_string = f'a {den_str}' if num == 1 else f'{num} {den_str}'
    elif num == 1:
        return_string = f'{whole} and a {den_str}'
    else:
        return_string = f'{whole} and {num} {den_str}'
    if num > 1:
        return_string += 's'
    return return_string


def pronounce_number_en(num, places=2, short_scale=True, scientific=False):
    """
    Convert a number to its spoken equivalent

    For example, '5.2' would return 'five point two'

    Args:
        num(float or int): the number to pronounce (under 100)
        places(int): maximum decimal places to speak
        short_scale (bool) : use short (True) or long scale (False)
            https://en.wikipedia.org/wiki/Names_of_large_numbers
        scientific (bool): pronounce in scientific notation
    Returns:
        (str): The pronounced number
    """
    if scientific:
        number = '%E' % num
        n, power = number.replace("+", "").split("E")
        power = int(power)
        if power != 0:
            # This handles negatives of powers separately from the normal
            # handling since each call disables the scientific flag
            return '{}{} times ten to the power of {}{}'.format(
                'negative ' if float(n) < 0 else '',
                pronounce_number_en(abs(float(n)), places, short_scale, False),
                'negative ' if power < 0 else '',
                pronounce_number_en(abs(power), places, short_scale, False))
    if short_scale:
        number_names = _NUM_STRING_EN.copy()
        number_names.update(_SHORT_SCALE_EN)
    else:
        number_names = _NUM_STRING_EN.copy()
        number_names.update(_LONG_SCALE_EN)

    digits = [number_names[n] for n in range(0, 20)]

    tens = [number_names[n] for n in range(10, 100, 10)]

    if short_scale:
        hundreds = [_SHORT_SCALE_EN[n] for n in _SHORT_SCALE_EN.keys()]
    else:
        hundreds = [_LONG_SCALE_EN[n] for n in _LONG_SCALE_EN.keys()]

    # deal with negatives
    result = ""
    if num < 0:
        result = "negative " if scientific else "minus "
    num = abs(num)

    try:
        # deal with 4 digits
        # usually if it's a 4 digit num it should be said like a date
        # i.e. 1972 => nineteen seventy two
        if len(str(num)) == 4 and isinstance(num, int):
            _num = str(num)
            # deal with 1000, 2000, 2001, 2100, 3123, etc
            # is skipped as the rest of the
            # functin deals with this already
            if _num[1:4] == '000' or _num[1:3] == '00' or int(_num[:2]) >= 20:
                pass
            elif _num[2:4] == '00':
                first = number_names[int(_num[:2])]
                last = number_names[100]
                return f"{first} {last}"
            else:
                first = number_names[int(_num[:2])]
                if _num[3:4] == '0':
                    last = number_names[int(_num[2:4])]
                else:
                    second = number_names[int(_num[2:3])*10]
                    last = f"{second} {number_names[int(_num[3:4])]}"
                return f"{first} {last}"
    except Exception as e:
        LOG.error('Exception in pronounce_number_en: {}' + repr(e))

    # check for a direct match
    if num in number_names:
        if num > 90:
            result += "one "
        result += number_names[num]
    else:
        def _sub_thousand(n):
            assert 0 <= n <= 999
            if n <= 19:
                return digits[n]
            elif n <= 99:
                q, r = divmod(n, 10)
                return tens[q - 1] + (f" {_sub_thousand(r)}" if r else "")
            else:
                q, r = divmod(n, 100)
                return (f"{digits[q]} hundred" + (f" and {_sub_thousand(r)}" if r else ""))

        def _short_scale(n):
            if n >= max(_SHORT_SCALE_EN.keys()):
                return "infinity"
            n = int(n)
            assert 0 <= n
            res = []
            for i, z in enumerate(_split_by(n, 1000)):
                if not z:
                    continue
                number = _sub_thousand(z)
                if i:
                    number += " "
                    number += hundreds[i]
                res.append(number)

            return ", ".join(reversed(res))

        def _split_by(n, split=1000):
            assert 0 <= n
            res = []
            while n:
                n, r = divmod(n, split)
                res.append(r)
            return res

        def _long_scale(n):
            if n >= max(_LONG_SCALE_EN.keys()):
                return "infinity"
            n = int(n)
            assert 0 <= n
            res = []
            for i, z in enumerate(_split_by(n, 1000000)):
                if not z:
                    continue
                number = pronounce_number_en(z, places, True, scientific)
                # strip off the comma after the thousand
                if i:
                    # plus one as we skip 'thousand'
                    # (and 'hundred', but this is excluded by index value)
                    number = number.replace(',', '')
                    number += f" {hundreds[i + 1]}"
                res.append(number)
            return ", ".join(reversed(res))

        result += _short_scale(num) if short_scale else _long_scale(num)
    # Deal with fractional part
    if num != int(num) and places > 0:
        result += " point"
        place = 10
        while int(num * place) % 10 > 0 and places > 0:
            result += f" {number_names[int(num * place) % 10]}"
            place *= 10
            places -= 1
    return result


def nice_time_en(dt, speech=True, use_24hour=False, use_ampm=False):
    """
    Format a time to a comfortable human format

    For example, generate 'five thirty' for speech or '5:30' for
    text display.

    Args:
        dt (datetime): date to format (assumes already in local timezone)
        speech (bool): format for speech (default/True) or display (False)=Fal
        use_24hour (bool): output in 24-hour/military or 12-hour format
        use_ampm (bool): include the am/pm for 12-hour format
    Returns:
        (str): The formatted time string
    """
    if use_24hour:
        # e.g. "03:01" or "14:22"
        string = dt.strftime("%H:%M")
    else:
        string = dt.strftime("%I:%M %p") if use_ampm else dt.strftime("%I:%M")
        if string[0] == '0':
            string = string[1:]  # strip leading zeros

    if not speech:
        return string

    # Generate a speakable version of the time
    if use_24hour:
        speak = ""

        # Either "0 8 hundred" or "13 hundred"
        if string[0] == '0':
            speak += f"{pronounce_number_en(int(string[0]))} "
            speak += pronounce_number_en(int(string[1]))
        else:
            speak = pronounce_number_en(int(string[:2]))

        speak += " "
        if string[3:5] == '00':
            speak += "hundred"
        elif string[3] == '0':
            speak += f"{pronounce_number_en(0)} "
            speak += pronounce_number_en(int(string[4]))
        else:
            speak += pronounce_number_en(int(string[3:5]))
    else:
        if dt.hour == 0 and dt.minute == 0:
            return "midnight"
        if dt.hour == 12 and dt.minute == 0:
            return "noon"
        # TODO: "half past 3", "a quarter of 4" and other idiomatic times

        if dt.hour == 0:
            speak = pronounce_number_en(12)
        elif dt.hour < 13:
            speak = pronounce_number_en(dt.hour)
        else:
            speak = pronounce_number_en(dt.hour - 12)

        if dt.minute == 0:
            if not use_ampm:
                return f"{speak} o'clock"
        else:
            if dt.minute < 10:
                speak += " oh"
            speak += f" {pronounce_number_en(dt.minute)}"

        if use_ampm:
            speak += " p.m." if dt.hour > 11 else " a.m."

    return speak
