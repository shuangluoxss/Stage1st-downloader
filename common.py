def second_to_timestr(t):
    if t < 60:
        return '%d秒' % round(t)
    elif t < 3600:
        return '%d分%d秒' % (t // 60, round(t) % 60)
    else:
        return '%d小时%d分%d秒' % (t // 3600, (t % 3600) % 60, round(t) % 60)

