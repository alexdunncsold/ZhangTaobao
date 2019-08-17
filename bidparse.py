from bid import Bid
from config import SANE_LOWER_BOUND, SANE_UPPER_BOUND
from facebookhandler import FacebookHandler as fb


def normalise_digits(comment_text):
    normalised_text = ''
    for char in comment_text:
        char_val = ord(char)
        if char_val == ord('0') or char_val == ord('o') or char_val == ord('O') or char_val == ord('〇') \
                or char_val == ord('０') or char_val == ord('ｏ') or char_val == ord('Ｏ'):
            normalised_text += '0'
        elif char_val == ord('1') or char_val == ord('一') or char_val == ord('１'):
            normalised_text += '1'
        elif char_val == ord('2') or char_val == ord('二') or char_val == ord('２'):
            normalised_text += '2'
        elif char_val == ord('3') or char_val == ord('三') or char_val == ord('３'):
            normalised_text += '3'
        elif char_val == ord('4') or char_val == ord('四') or char_val == ord('４'):
            normalised_text += '4'
        elif char_val == ord('5') or char_val == ord('五') or char_val == ord('５'):
            normalised_text += '5'
        elif char_val == ord('6') or char_val == ord('六') or char_val == ord('６'):
            normalised_text += '6'
        elif char_val == ord('7') or char_val == ord('七') or char_val == ord('７'):
            normalised_text += '7'
        elif char_val == ord('8') or char_val == ord('八') or char_val == ord('８'):
            normalised_text += '8'
        elif char_val == ord('9') or char_val == ord('九') or char_val == ord('９'):
            normalised_text += '9'
        elif char_val == ord(','):
            pass
        else:
            normalised_text += char
    return normalised_text


def is_sane_value(candidate_string):
    try:
        bid_amount = int(candidate_string)
    except ValueError:
        return False
    return SANE_LOWER_BOUND <= bid_amount <= SANE_UPPER_BOUND


def text_parse(comment_text):
    # returns the first sanely-valued number in a comment
    comment_text = normalise_digits(comment_text)
    bid_value_text = ''
    for char in comment_text + ' ':
        if char.isdigit():
            bid_value_text += char
        elif is_sane_value(bid_value_text):
            return int(bid_value_text)
        else:
            bid_value_text = ''
    raise ValueError('parse_bid(): No sane value could be parsed from comment_text=' + comment_text)


def comment_parse(comment):
    author = fb.get_comment_author(comment)
    comment_text = fb.get_comment_text(comment)
    timestamp = fb.get_comment_timestamp(comment)

    # distinguish automated bids from manual bids in dev configuration
    if '(autobid)' in comment_text:
        author += '/dev'

    bid_value = text_parse(comment_text)
    return Bid(author, bid_value, timestamp)
