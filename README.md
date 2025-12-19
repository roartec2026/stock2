# Stock OHLC Analysis Admin Dashboard

A professional web-based admin dashboard for analyzing stock OHLC (Open, High, Low, Close) data using Streamlit and Python.

## Features

- **🌐 Modern Web UI**: Beautiful, responsive web interface built with Streamlit
- **⏱️ Timeframe Selection**: Hourly, Daily, Weekly, Monthly
- **📊 Reference Time Logic**: Only fetches previous completed candles (no current/incomplete candles)
- **🎨 Theme Support**: Dark/Light theme (via Streamlit settings)
- **🔄 Auto-Refresh**: Optional automatic data refresh every 10 seconds
- **💾 CSV Export**: Export data to CSV with download option
- **📈 Statistics**: Real-time statistics (Average Open, High, Low, Close)
- **⚙️ Settings Persistence**: Saves auto-refresh preferences

## Quick Start

### Option 1: Use Launcher Scripts (Recommended)

The easiest way to run the dashboard is using the launcher scripts that automatically check and install required packages:

**Windows:**
```bash
run.bat
```
Or double-click `run.bat` in File Explorer

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Cross-platform (Python):**
```bash
python run.py
```

### Option 2: Manual Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the dashboard:
```bash
streamlit run dashboard.py
```

The dashboard will automatically open in your default web browser at `http://localhost:8501`

## Usage

### Web Interface

1. **Enter Stock Symbol**: Type a stock ticker (e.g., AAPL, MSFT, GOOGL) in the input field
2. **Select Timeframe**: Choose from Hourly, Daily, Weekly, or Monthly using the sidebar radio buttons
3. **Set Reference Date**: Select the reference date (and time for Hourly timeframe)
4. **Set Candle Count**: Enter the number of previous completed candles to fetch
5. **Fetch Data**: Click the "🚀 Fetch Data" button
6. **View Results**: The OHLC data table and statistics will be displayed
7. **Export CSV**: Click "📥 Export to CSV" to save the data

### Sidebar Features

- **Timeframe Selection**: Radio buttons to switch between timeframes
- **Auto-Refresh Toggle**: Enable/disable automatic data refresh (every 10 seconds)
- **Theme**: Use Streamlit's built-in theme switcher (☰ menu → Settings → Theme)

## Project Structure

```
project/
├── dashboard.py        # Main Streamlit application
├── run.py             # Python launcher (checks & installs packages)
├── run.bat            # Windows launcher script
├── run.sh             # Linux/Mac launcher script
├── settings.json       # Saved preferences (auto-generated)
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── exports/           # CSV export directory (auto-generated)
    └── *.csv
```

## Data Logic

The dashboard implements strict candle selection logic:

1. **Reference Time**: 
   - Hourly: Uses date + time
   - Daily/Weekly/Monthly: Uses date only

2. **Candle Filtering**:
   - Only candles with `index < reference_time` are included
   - Takes the last `count` candles from filtered data
   - Never includes current/incomplete candles

This ensures:
- ✅ Correct historical data
- ✅ Stable averages
- ✅ No repainting issues

## Settings

Settings are automatically saved to `settings.json`:
- `theme`: "dark" or "light" (handled by Streamlit)
- `auto_refresh`: true or false

## CSV Export

CSV files are saved to the `exports/` directory with the format:
```
{symbol}_{timeframe}_{timestamp}.csv
```

Columns: `Period,Open,High,Low,Close`

You can download the CSV directly from the web interface after exporting.

## Requirements

- Python 3.7 or higher
- Streamlit 1.28.0 or higher
- yfinance 0.2.28 or higher
- pandas 2.0.0 or higher

## Troubleshooting

### Dashboard doesn't open automatically
- Manually navigate to `http://localhost:8501` in your web browser

### Port 8501 is already in use
- Streamlit will automatically try the next available port (8502, 8503, etc.)
- Check the terminal output for the correct URL

### Data fetch fails
- Verify the stock symbol is correct
- Check your internet connection
- Ensure the reference date is not too far in the future
- Some stocks may have limited historical data

## License

This project is provided as-is for educational and professional use.
