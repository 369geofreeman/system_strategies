def transProb(data, scope):
    # Transition probabilities to indicate bullish or bearish trend
    # returns  (('Bull'/'Bear'), %)
    green_to_green = 0
    green_to_red = 0
    red_to_red = 0
    red_to_green = 0
    green_volume = 0
    red_volume = 0

    index = data.index[0]

    for idx, row in data.iterrows():
        if idx == index or idx >= (index + scope-1):
            continue
        # Check for green candle
        if data.loc[idx, 'close'] > data.loc[idx-1, 'close']:
            # Transition from green to green
            if data.loc[idx, 'close'] < data.loc[idx+1, 'close']:
                green_to_green += 1
                green_volume += data.loc[idx, 'volume']
            # transition from green to red
            else:
                green_to_red += 1
                green_volume += data.loc[idx, 'volume']
        # Check for red candle
        else:
            # Transition from red to red
            if data.loc[idx, 'close'] > data.loc[idx+1, 'close']:
                red_to_red += 1
                red_volume += data.loc[idx, 'volume']
            # Transition from red to green
            else:
                red_to_green += 1
                red_volume += data.loc[idx, 'volume']

    # Return transitions
    total_green_candles = green_to_green + red_to_green
    total_red_candles = red_to_red + green_to_red
    total_volume = data['volume'].sum()
    # Dominance
    green_volume_dominance = round(green_volume / total_volume, 2)
    red_volume_dominance = round(red_volume / total_volume, 2)
    green_dominance = round(total_green_candles * green_volume_dominance, 2)
    red_dominance = round(total_red_candles * red_volume_dominance, 2)
    total_green_dominance = round((green_dominance / (green_dominance + red_dominance))*100, 2)
    total_red_dominance = round((red_dominance / (green_dominance + red_dominance))*100, 2)

    if total_green_dominance >= total_red_dominance:
        return ('Bull', total_green_dominance)
    else:
        return ('Bear', total_red_dominance)