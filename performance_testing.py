from datetime import datetime, timedelta


def ptest(description, f):
    start_time = datetime.utcnow()
    return_value = f()
    stop_time = datetime.utcnow()
    print(f'{description} took {(stop_time - start_time) / timedelta(milliseconds=1)}')
    return return_value


def pstart(description):
    return (description, datetime.utcnow())


def pstop(pstart):
    stop_time = datetime.utcnow()
    print(f'{pstart[0]} took {(stop_time - pstart[1]) / timedelta(milliseconds=1)}ms')
