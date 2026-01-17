# Stock ROARSTAR Analysis Admin Dashboard (Branch: roarstar)

A professional web-based admin dashboard for analyzing stock ROARSTAR (Open, High, Low, Close) data using Streamlit and Python. Features advanced statistical calculations including forward-looking rolling averages, standard deviations, and upper/lower bands.

## Features

- **🌐 Modern Web UI**: Beautiful, responsive web interface built with Streamlit
- **⏱️ Timeframe Selection**: Hourly, Daily, Weekly, Monthly with predefined time slots
- **📊 Reference Time Logic**: Only fetches previous completed candles (no current/incomplete candles)
- **🎲 Random Number Feature**: Configurable random number column with T161/T162 bounds and padding support
- **📈 Advanced Statistics**: 
  - Forward-looking Running Average (Open) with 20-row rolling window
  - Forward-looking Running STDDEV.S (Open) with sample standard deviation
  - Upper Bands (UB): ×2.8, ×2.1, ×1.4, ×0.7, ×0.35
  - Lower Bands (LB): ×2.8, ×2.1, ×1.4, ×0.7, ×0.35
- **🎨 Theme Support**: Dark/Light theme (via Streamlit settings)
- **🔄 Auto-Refresh**: Optional automatic data refresh every 10 seconds
- **💾 CSV Export**: Export data to CSV with all calculated columns and download option
- **📊 Statistics Dashboard**: Real-time statistics (Average Open, High, Low, Close)
- **🌍 Multi-Market Support**: Automatic currency detection (INR for Indian stocks, USD for others)
- **📋 Predefined Symbols**: Quick selection for popular stocks and indices (NIFTY 50, SENSEX, US stocks, etc.)
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
6. **View Results**: The ROARSTAR data table and statistics will be displayed
7. **Export CSV**: Click "📥 Export to CSV" to save the data

### Sidebar Features

- **Timeframe Selection**: Radio buttons to switch between timeframes (Hourly, Daily, Weekly, Monthly)
- **Random Number Feature**: 
  - Enable/disable random number column
  - Configure T161 (upper bound) and T162 (lower bound)
  - Lock settings to activate the column
  - Optional padding for calculations when data is insufficient
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
   - Hourly: Uses date + time (with predefined time slots: 09:15, 10:15, 11:15, etc.)
   - Daily/Weekly/Monthly: Uses date only

2. **Candle Filtering**:
   - Only candles with `index < reference_time` are included
   - Takes the last `count` candles from filtered data
   - Never includes current/incomplete candles

3. **Statistical Calculations**:
   - **Running Average (Open)**: Forward-looking rolling average of 20 Open prices
     - Row 1: average of rows 1-20
     - Row 2: average of rows 2-21
     - Row 3: average of rows 3-22, etc.
   - **Running STDDEV.S (Open)**: Forward-looking sample standard deviation (n-1) of 20 Open prices
   - **Upper/Lower Bands**: Calculated as Average ± (STDDEV.S × multiplier)
     - Multipliers: 2.8, 2.1, 1.4, 0.7, 0.35
   - **Random Number Padding**: When fewer than 20 forward values exist, can pad with random numbers

This ensures:
- ✅ Correct historical data
- ✅ Stable averages
- ✅ No repainting issues
- ✅ Forward-looking calculations (no look-ahead bias)

## Random Number Feature

The dashboard includes an advanced Random Number feature:

1. **Enable the Feature**: Check "Enable Random Number Column" in the sidebar
2. **Configure Bounds**: 
   - Set T161 (upper bound, default: 100.0)
   - Set T162 (lower bound, default: 0.0)
   - T161 must be greater than T162
3. **Lock Settings**: Click "💾 Save & Lock" to activate the column
4. **Random Padding**: Optional feature to pad calculations with random numbers when data is insufficient
   - Enable "Use Random Numbers For Padding"
   - Set "Random Padding Count" (default: 20)

The random number is calculated using: `random.random() * (T161 - T162) + T162`

## Settings

Settings are automatically saved to `settings.json`:
- `theme`: "dark" or "light" (handled by Streamlit)
- `auto_refresh`: true or false

## CSV Export

CSV files are saved to the `exports/` directory with the format:
```
{symbol}_{timeframe}_{timestamp}.csv
```

**Exported Columns:**
- `Period`: Date/time of the candle
- `Open, High, Low, Close`: OHLC price data
- `Random Number`: (if feature enabled) Random number column
- `Running Average (Open)`: Forward-looking 20-row rolling average
- `Running STDDEV.S (Open)`: Forward-looking 20-row sample standard deviation
- `UB × 2.8, UB × 2.1, UB*1.4, UB*.7, UB*.35`: Upper bands
- `LB*2.8, LB*2.1, LB*1.4, LB*.7, LB*.35`: Lower bands

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
