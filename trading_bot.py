

import ccxt
import time
import pandas as pd
import ta

# Ініціалізація клієнта Binance Futures Testnet
api_key = ''
api_secret = ''

exchange = ccxt.binanceusdm({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    },
})
exchange.set_sandbox_mode(True)  # Увімкнення тестового режиму

symbol = 'BTC/USDT'  # Тикер для торгівлі
timeframe = '15m'  # Часовий інтервал для аналізу
trade_amount = 0.001  # Сума для торгівлі (в BTC)
rsi_period = 14  # Період для індикатора RSI

# Функція для отримання даних ринку
def fetch_ohlcv(symbol, timeframe):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    return df

# Функція для обчислення індикаторів
def calculate_indicators(df):
    df['MA50'] = df['close'].rolling(window=50).mean()  # Довгострокова ковзна середня
    df['MA20'] = df['close'].rolling(window=20).mean()  # Короткострокова ковзна середня
    df['RSI'] = ta.momentum.RSIIndicator(df['close'], rsi_period).rsi()  # RSI
    return df

# Функція для виконання торгових операцій
def execute_trade(signal, symbol):
    last_price = exchange.fetch_ticker(symbol)['last']  # Отримуємо останню ціну
    if signal == 'buy':
        print(f"Купівля {symbol}")
        order = exchange.create_market_buy_order(symbol, trade_amount)
        print("Ордер на купівлю виконаний:", order)
        
        # Встановлюємо тейк-профіт і стоп-лос
        take_profit_price = last_price * 1.05  # Тейк-профіт на 5% вище
        stop_loss_price = last_price * 0.95    # Стоп-лос на 5% нижче
        
        # Ордер на тейк-профіт
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'sell', trade_amount, None, {
            'stopPrice': take_profit_price
        })
        
        # Ордер на стоп-лос
        exchange.create_order(symbol, 'STOP_MARKET', 'sell', trade_amount, None, {
            'stopPrice': stop_loss_price
        })
        
    elif signal == 'sell':
        print(f"Продаж {symbol}")
        order = exchange.create_market_sell_order(symbol, trade_amount)
        print("Ордер на продаж виконаний:", order)
        
        # Встановлюємо тейк-профіт і стоп-лос для короткої позиції
        take_profit_price = last_price * 0.95  # Тейк-профіт на 5% нижче
        stop_loss_price = last_price * 1.05    # Стоп-лос на 5% вище
        
        # Ордер на тейк-профіт
        exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', 'buy', trade_amount, None, {
            'stopPrice': take_profit_price
        })
        
        # Ордер на стоп-лос
        exchange.create_order(symbol, 'STOP_MARKET', 'buy', trade_amount, None, {
            'stopPrice': stop_loss_price
        })

# Основна функція для запуску бота
def run_bot():
    while True:
        try:
            # Отримуємо поточні дані ринку
            df = fetch_ohlcv(symbol, timeframe)
            df = calculate_indicators(df)
            
            last_row = df.iloc[-1]  # Останній рядок з даними
            
            # Торгові умови на основі ковзних середніх і RSI
            if last_row['MA20'] > last_row['MA50'] and last_row['RSI'] < 30:
                execute_trade('buy', symbol)  # Купівля, коли ринок перепроданий і тренд на зростання
            elif last_row['MA20'] < last_row['MA50'] and last_row['RSI'] > 70:
                execute_trade('sell', symbol)  # Продаж, коли ринок перекуплений і тренд на спадання
            else:
                print("Ніяких дій не потрібно")
        
        except Exception as e:
            print("Сталася помилка під час роботи бота:", e)

        # Чекаємо 15 хвилин до наступної перевірки ринку
        time.sleep(15 * 60)

# Запуск бота
run_bot()
