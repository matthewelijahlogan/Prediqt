import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {
  ActivityIndicator,
  FlatList,
  Image,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import {
  fetchNews,
  fetchPrediction,
  fetchQuote,
  fetchTickerTape,
} from './src/api/client';

const HORIZONS = ['hour', 'day', 'week', 'month'];

export default function App() {
  const [ticker, setTicker] = useState('AAPL');
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [quote, setQuote] = useState(null);
  const [predictions, setPredictions] = useState({});
  const [news, setNews] = useState([]);
  const [tickerTape, setTickerTape] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadAppData = useCallback(async symbol => {
    setLoading(true);
    setError('');

    try {
      const [quoteData, tickerData, newsData] = await Promise.all([
        fetchQuote(symbol),
        fetchTickerTape(),
        fetchNews(),
      ]);

      setQuote(quoteData);
      setTickerTape(tickerData.tickers || []);
      setNews(newsData.headlines || []);

      const predictionEntries = await Promise.all(
        HORIZONS.map(async horizon => {
          const p = await fetchPrediction(symbol, horizon);
          return [horizon, p];
        }),
      );

      setPredictions(Object.fromEntries(predictionEntries));
      setSelectedTicker(symbol);
    } catch (e) {
      setError(e.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAppData('AAPL');
  }, [loadAppData]);

  const onPredictPress = useCallback(() => {
    const symbol = ticker.trim().toUpperCase();
    if (!symbol) {
      return;
    }
    loadAppData(symbol);
  }, [loadAppData, ticker]);

  const topNews = useMemo(() => news.slice(0, 10), [news]);

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor="#f3f7fc" />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.brandRow}>
          <Image source={require('./assets/icon.png')} style={styles.logo} />
          <View>
            <Text style={styles.title}>PredIQT</Text>
            <Text style={styles.subtitle}>AI Market Forecast + Live Quote</Text>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Ticker</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={ticker}
              autoCapitalize="characters"
              onChangeText={setTicker}
              placeholder="AAPL"
              placeholderTextColor="#8a96a8"
            />
            <Pressable style={styles.button} onPress={onPredictPress}>
              <Text style={styles.buttonText}>Predict</Text>
            </Pressable>
          </View>
          {loading ? <ActivityIndicator color="#1f6feb" /> : null}
          {error ? <Text style={styles.error}>{error}</Text> : null}
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Predictions ({selectedTicker})</Text>
          {HORIZONS.map(horizon => {
            const value = predictions[horizon]?.predicted_next_close;
            return (
              <View key={horizon} style={styles.rowBetween}>
                <Text style={styles.label}>{horizon.toUpperCase()}</Text>
                <Text style={styles.value}>
                  {typeof value === 'number' ? `$${value.toFixed(2)}` : '-'}
                </Text>
              </View>
            );
          })}
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Quote ({selectedTicker})</Text>
          <InfoRow label="Price" value={formatMoney(quote?.price)} />
          <InfoRow label="Change" value={formatMoney(quote?.change)} />
          <InfoRow label="% Change" value={formatPercent(quote?.percent_change)} />
          <InfoRow label="Volume" value={formatInt(quote?.volume)} />
          <InfoRow label="Market Cap" value={formatInt(quote?.market_cap)} />
          <InfoRow label="Sector" value={quote?.sector || '-'} />
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Ticker Tape</Text>
          <FlatList
            data={tickerTape}
            keyExtractor={item => item.symbol}
            horizontal
            showsHorizontalScrollIndicator={false}
            renderItem={({item}) => (
              <Pressable
                style={styles.tickerPill}
                onPress={() => {
                  setTicker(item.symbol);
                  loadAppData(item.symbol);
                }}>
                <Text style={styles.tickerText}>{item.symbol}</Text>
                <Text style={styles.tickerPrice}>{String(item.price)}</Text>
              </Pressable>
            )}
          />
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Business Headlines</Text>
          {topNews.length === 0 ? (
            <Text style={styles.muted}>No headlines available.</Text>
          ) : null}
          {topNews.map(headline => (
            <Text key={headline} style={styles.newsItem}>
              * {headline}
            </Text>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoRow({label, value}) {
  return (
    <View style={styles.rowBetween}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

function formatMoney(value) {
  if (typeof value !== 'number') {
    return '-';
  }
  return `$${value.toFixed(2)}`;
}

function formatPercent(value) {
  if (typeof value !== 'number') {
    return '-';
  }
  return `${value.toFixed(2)}%`;
}

function formatInt(value) {
  if (typeof value !== 'number') {
    return '-';
  }
  return value.toLocaleString();
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#f3f7fc',
  },
  content: {
    padding: 16,
    gap: 12,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 4,
  },
  logo: {
    width: 48,
    height: 48,
    borderRadius: 10,
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: '#0a2540',
  },
  subtitle: {
    color: '#4b6584',
    marginBottom: 4,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: '#dce6f4',
    gap: 8,
  },
  sectionTitle: {
    fontWeight: '700',
    fontSize: 17,
    color: '#102a43',
  },
  inputRow: {
    flexDirection: 'row',
    gap: 8,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#bfd2ea',
    borderRadius: 10,
    paddingHorizontal: 12,
    height: 44,
    color: '#102a43',
  },
  button: {
    backgroundColor: '#1f6feb',
    paddingHorizontal: 16,
    borderRadius: 10,
    justifyContent: 'center',
  },
  buttonText: {
    color: '#fff',
    fontWeight: '700',
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    color: '#486581',
    fontWeight: '600',
  },
  value: {
    color: '#0a2540',
    fontWeight: '700',
  },
  tickerPill: {
    backgroundColor: '#eff6ff',
    borderColor: '#b6d4fe',
    borderWidth: 1,
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginRight: 8,
  },
  tickerText: {
    color: '#1849a9',
    fontWeight: '800',
  },
  tickerPrice: {
    color: '#486581',
    fontWeight: '700',
  },
  newsItem: {
    color: '#243b53',
    marginBottom: 6,
  },
  muted: {
    color: '#829ab1',
  },
  error: {
    color: '#b42318',
    fontWeight: '600',
  },
});
