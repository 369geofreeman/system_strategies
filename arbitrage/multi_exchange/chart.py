import matplotlib.pyplot as plt


def show_chart(data):

    x = [i for i in range(len(data["Binance"]["bid_stream"]))]
    y1 = data["Ftx"]["bid_stream"][-len(x):]
    y2 = data["Kraken"]["bid_stream"][-len(x):]

    plt.plot(x, data["Binance"]["bid_stream"], 'b', label='Binance')
    plt.plot(x, y1, 'r', label='Ftx')
    plt.plot(x, y2, 'g', label='Kraken')
    plt.grid()
    plt.legend()
    plt.show()