from datetime import datetime
import re

import auctionpost
import constraintset
import facebookgroup

test_post_text = '''
    競標~ 
# 戰友編號：436

茶廠：三合堂囍字號女兒茶
品名：極品古樹茶
年份：2007年
規格：400克/1餅
生熟：生茶
茶倉：乾倉，茶香，餅邊、餅背面稍許泛茶油
數量：一標一餅
運費：無論成交多少運費一律100元(台灣本島)，無貨到付款方式
競標：6月26日 22點00分59秒準時結標（臉書顯示22:01分過分不算）
同時又同價，以先出價者得標。
起標1元，每步+100 無貨到付款
標到者請在三日內完成匯款，歡迎下標
誠實賣家每筆交易均開立發票，保證正品，如賣仿冒品願意無條件退貨，同時負擔所有運費。
'''

#separation characters
seps = ' ：: —】'


def strip_separators(text):
    for c in seps:
        text = text.replace(c, '')
    return text


def parse_seller(text):
    pass


def parse_producer(text):
    try:
        producer = strip_separators(re.search(f'(?<=茶廠)[{seps}]*.*', text)[0])
    except:
        return 'unable to parse'

    return producer


def parse_production(text):
    try:
        production = strip_separators(re.search(f'(?<=品名)[{seps}]*.*', text)[0])
    except:
        return 'unable to parse'

    return production


def parse_production_year(text):
    try:
        production_year = strip_separators(re.search(f'(?<=年份)[{seps}]*\d\d\d\d', text)[0])
    except:
        return 'unable to parse'

    return production_year


def parse_weight(text):
    try:
        production_year = strip_separators(re.search(f'(?<=規格)[{seps}]*\d*(?=克)', text)[0])
    except:
        return 'unable to parse'

    return production_year


def parse_tea_type(text):
    try:
        tea_type = strip_separators(re.search(f'(?<=生熟).*', text)[0])
    except ValueError:
        return 'unable to parse'

    if tea_type == '生茶':
        return 'sheng'
    else:
        return 'shou/other'


def parse_storage_type(text):
    try:
        storage_type = re.search('(?<=茶倉[：:]).*(?=倉)', text)

        if not storage_type:
            storage_type = re.search('(?<=茶倉).*(?=倉)', text)

        if not storage_type:
            raise ValueError()
    except ValueError:
        storage_type = 'unable to parse'

    storage_type_translations = {
        '乾': 'dry',
    }

    if storage_type[0] in storage_type_translations:
        storage_type = storage_type_translations[storage_type[0]]

    return storage_type


def parse_expiry(text):
    try:
        expiry_line = re.search('(?<=競標[：:]).*', text)[0]
        date_part = re.search('\d{1,2}月\d{1,2}日', expiry_line)[0]

        month = int(re.search('\d{1,2}(?=月)', date_part)[0])
        day = int(re.search('\d{1,2}(?=日)', date_part)[0])

        if re.search('\d{1,2}點\d{2}分', expiry_line):
            time_format = 'HH點MM分'
            time_part = re.search('\d{1,2}點\d{2}分', expiry_line)[0]
        elif re.search('\d{1,2}[：:]\d{2}', expiry_line):
            time_format = 'HH:MM'
            time_part = re.search('\d{1,2}[：:]\d{2}', expiry_line)[0]
        else:
            raise ValueError()

        if time_format == 'HH點MM分':
            hour = int(re.search('\d{1,2}(?=點)', time_part)[0])
            minute = int(re.search('\d{1,2}(?=分)', time_part)[0])
        elif time_format == 'HH:MM':
            hour = int(re.search('\d{1,2}(?=[：:])', time_part)[0])
            minute = int(re.search('(?<=[：:])\d{1,2}', time_part)[0])
        else:
            raise ValueError()

        expiry = datetime(datetime.now().year, month, day, hour, minute)
    except ValueError:
        return 'unable to parse'

    return expiry


def parse_bid_step(text):
    try:
        bid_step = re.search('(?<=每步)\+?\d*', text)[0].replace('+','')
    except:
        return 'could not parse'

    return int(bid_step)


def parse_minimum_bid(text):
    try:
        minimum_bid = re.search('(?<=起標)\d*(?=元)', text)[0].replace('+', '')
    except:
        return 'could not parse'

    return int(minimum_bid)


print(f'prodder:{parse_producer(test_post_text)}\n'
      f'prod:{parse_production(test_post_text)}\n'
      f'year:{parse_production_year(test_post_text)}\n'
      f'weight:{parse_weight(test_post_text)}g\n'
      f'type:{parse_tea_type(test_post_text)}\n'
      f'storage:{parse_storage_type(test_post_text)}\n'
      f'expiry: {parse_expiry(test_post_text)}\n'
      f'min bid: {parse_minimum_bid(test_post_text)}\n'
      f'bid step: {parse_bid_step(test_post_text)}')