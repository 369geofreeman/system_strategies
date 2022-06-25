import cryptocompare as cc
from time import sleep
import numpy as np
import pandas as pd
import heapq
import threading
import time
np.seterr(divide='ignore', invalid='ignore')


usdtpairs = np.array(['LINK', 'RFUEL', 'CWS', 'MSWAP', 'LAYER', 'EOSC', 'NWC', 'KLV', 'BOLT', 'SYLO', 'ZEE', 'UNI', 'SNX', 'XCUR', 'USDN', 'TKY', 'CHR', 'VRA', 'MASK', 'COTI', 'NOIA', 'SHR', 'DOGE', 'SPI', 'SUSD', 'TOMO', 'SRK', 'AVAX', 'BCHA', 'REN', 'KCS', 'IOST', 'DERO', 'UBXT', 'AOA', 'DYP', 'POL', 'BOSON', 'MTV', 'DAG', 'TCP', 'GO', 'USDC', 'ICP', 'OXEN', 'DFI', 'TOWER', 'PHA', 'STRONG', 'TEL', 'ETH3L', 'WEST', 'GHX', 'BOA', 'MHC', 'KAI', 'QNT', 'VAI', 'POLX', 'WAVES', 'KAT', 'XSR', 'XHV', 'SENSO', 'THETA', 'KRL', 'CGG', 'FRONT', 'UNFI', 'RLY', 'VIDT', 'PRE', 'WAXP', 'BTMX', 'WXT', 'STC', 'MXW', 'ALEPH', 'GMB', 'EOS', 'KDA', 'CAS', 'PDEX', 'GSPI', 'DASH', 'TOKO', 'LON', 'LTX', 'ORAI', 'REV', 'BAX', 'DIA', 'NEO', 'UMA', 'LOCG', 'CUDOS', 'MITX', 'SUKU', 'LYXe', 'AVA', 'ETC', 'STX', 'XTZ', 'LUNA', 'ACOIN', 'JAR', 'SUTER', 'CKB', 'PUNDIX', 'CIX100', 'ZEC', 'CBC', 'HORD', 'UBX', 'FKX', 'HAI', 'WOM', 'SAND', 'SXP', 'PMGT', 'TRIAS', 'ZEN', 'ALGO', 'BCH', 'BTC', 'DGB', 'CARD', 'HTR', 'REVV', 'BAT', 'AAVE', 'BNS', 'ZIL', 'BEPRO', 'HT', 'PCX', 'COMB', 'PLU', 'MIR', 'XYM', 'GOVI', 'LTC', 'XRP', 'GAS', 'ETH3S', 'BNB', 'DODO', 'MKR', 'WIN', 'CHZ', 'XMR', 'DOT', 'YFI', 'MAN', 'BSV', 'FIL', 'VELO', 'CAKE', 'ROSE', 'SERO', 'cUSD', 'ADA', 'SHIB', 'CRV', 'MLK', 'ONT', 'MAP', 'XDB', 'ARX', 'BTC3S', 'AKRO', 'VSYS', 'STND', 'ETH', 'FORTH', 'DMG', 'FTM', 'LYM', 'EWT', 'TRX', 'DAO', 'TARA', 'VID', 'JST', 'UOS', 'FLUX', 'SUSHI', 'BTC3L', 'BTT', 'BLOC', 'API3', 'FLy', 'SUN', 'REAP', 'NIM', 'DSLA', 'CRO', 'ARPA', 'FORESTPLUS', 'LOC', 'HYDRA', 'ORBS', 'LRC', 'FRM', 'SWINGBY', 'SKEY', 'COMP', 'ACE', 'PHNX', 'XEM', 'ENQ', 'AMPL', 'USDJ', 'GOM2', 'GRT', 'ONE', '1INCH', 'CELO', 'DEGO', 'MANA', 'FCL', 'POLK', 'ORN', 'BRG', 'NANO', 'CTI', 'OMG', 'VET', 'KSM', 'PIVX', 'PROPS', 'ETN', 'LABS', 'CARR', 'ENJ', 'EQZ', 'SDT', 'GRIN', 'ANKR', 'IDEA', 'ANC', 'RFOX', 'XDC', 'XLM', 'DAPPT', 'RNDR', 'SHA', 'BUY', 'ATOM'])

# usdtpairs = usdtpairs[:10]

# usdtpairs = usdtpairskucoin = [x['fsym'] for x in cc.get_pairs() if x['tsym']=='USDT']


def createDF(name_lst, cormat, topk=10):
    lst = []
    max_val = []

    for x in cormat:
        idx = heapq.nlargest(topk+1, range(len(x)), x.take)
        max_val.append(x[0])
        names = []

        for i in idx:
            names.append("{}({})".format(usdtpairs[i], x[i]))
        lst.append(np.array(names))
    lst = np.array(lst)
    lst = lst[:, 1:]
    name_lst = np.array(name_lst)

    idx = np.array(max_val).argsort()[::-1]

    lst = lst[idx]
    name_lst = name_lst[idx]

    df = pd.DataFrame(lst, index=['{}'.format(x) for x in name_lst])  #, columns = ['{}/{}'.format(x,quote) for x in lst]
    df.to_csv('arb.csv')


prices_list = []
base_list = []


def getpricearray(base, quote):
    time = 4
    prices = []
    try:
        data = cc.get_historical_price_hour(base, quote, limit=time, exchange='Kucoin')
        assert len(data) == time+1
        for d in data:
            prices.append(d['close'])
        prices_list.append(prices)
        base_list.append(base)

    except Exception as e:
        pass


def threaded(lst, quote):
    global prices_list, base_list

    threadarr = []
    for base in list(lst)[:]:
        t = threading.Thread(target=getpricearray, args=(base, quote))
        threadarr.append(t)

    for t in threadarr:
        time.sleep(0.5)
        t.start()

    for t in threadarr:
        t.join()

    cormat = np.corrcoef(prices_list)

    return np.round(cormat, 3), base_list


def corelation(lst, quote):
    price_lst = []
    time = 10
    base_lst = []

    for base in lst:

        try:
            print("\r{}      ".format(base), end='')
            data = cc.get_historical_price_hour(base, quote, limit=time, exchange='Kucoin')
            assert len(data) == time+1
            prices = []

            for d in data:
                prices.append(d['close'])

            price_lst.append(prices)
            base_lst.append(base)

        except Exception as e:
            pass

    price_lst = np.array(price_lst)

    cormat = np.corrcoef(price_lst)

    return np.round(cormat, 3), base_lst


cormat, lst = corelation(usdtpairs, 'USDT')
createDF(lst, cormat)