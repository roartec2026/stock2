"""
Roarstar Stock Analysis Admin Dashboard
A professional web-based admin dashboard for analyzing Roarstar stock data using Streamlit.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import time
import random
from datetime import datetime, date, time as dt_time
from typing import Optional, Tuple

# Constants
SETTINGS_FILE = "settings.json"
EXPORTS_DIR = "exports"

# Timeframe mapping
TIMEFRAMES = {
    "Hourly": ("1h", "7d"),
    "Daily": ("1d", "3mo"),
    "Weekly": ("1wk", "1y"),
    "Monthly": ("1mo", "3y")
}

# Predefined Time Slots (for Hourly timeframe)
PREDEFINED_TIMES = {
    "09:15": dt_time(9, 15),
    "10:15": dt_time(10, 15),
    "11:15": dt_time(11, 15),
    "12:15": dt_time(12, 15),
    "13:15": dt_time(13, 15),
    "14:15": dt_time(14, 15),
    "15:15": dt_time(15, 15),
}

# Predefined Stock Symbols
PREDEFINED_SYMBOLS = {
    "NIFTY 50": "^NSEI",
    "SBIN": "SBIN.NS",
    "ITC": "ITC.NS",
    "MARUTI": "MARUTI.NS",
    "NIFTY BANK": "^NSEBANK",
    "KOTAKBANK": "KOTAKBANK.NS",
    "TITAN": "TITAN.NS",
    "CIPLA": "CIPLA.NS",
    "ONGC": "ONGC.NS",
    "WIPRO": "WIPRO.NS",
    "JSWSTEEL": "JSWSTEEL.NS",
    "NTPC": "NTPC.NS",
    "INFY": "INFY.NS",
    "MOSCHIP": "MOSCHIP.NS",
    "LTFOODS": "LTFOODS.NS",
    "CNBK": "CNBK.NS",
    "ADANIPORTS": "ADANIPORTS.NS",
    "INDIGO": "INDIGO.NS",
    "GRANULES": "GRANULES.NS",
    "COALINDIA": "COALINDIA.NS",
    "POWERGRID": "POWERGRID.NS",
    "BPCL": "BPCL.NS",
    "M&M": "M&M.NS",
    "TATAMOTORS": "TATAMOTORS.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "AXISBANK": "AXISBANK.NS",
    "SENSEX": "^BSESN",
    # Popular US stocks
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "GOOGL": "GOOGL",
    "TSLA": "TSLA",
    "AMZN": "AMZN",
}

# Ensure exports directory exists
os.makedirs(EXPORTS_DIR, exist_ok=True)


class DashboardSettings:
    """Manages application settings persistence."""
    
    @staticmethod
    def load_settings() -> dict:
        """Load settings from JSON file."""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"theme": "dark", "auto_refresh": False}
    
    @staticmethod
    def save_settings(settings: dict):
        """Save settings to JSON file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            st.error(f"Error saving settings: {e}")


class DataFetcher:
    """Handles fetching and processing stock data."""
    
    @staticmethod
    def validate_and_suggest_symbol(symbol: str) -> tuple[str, Optional[str]]:
        """
        Validate symbol and suggest corrections for common mistakes.
        Returns: (corrected_symbol, suggestion_message)
        """
        symbol_upper = symbol.upper().strip()
        
        # Check if it's in predefined symbols (reverse lookup)
        for name, yf_symbol in PREDEFINED_SYMBOLS.items():
            if symbol_upper == yf_symbol.upper() or symbol_upper == name.upper():
                return yf_symbol, None  # Already correct, no suggestion needed
        
        # Common Indian index mappings
        indian_indices = {
            'NIFTY50': '^NSEI',
            'NIFTY': '^NSEI',
            'NIFTY 50': '^NSEI',
            'NIFTY50.NS': '^NSEI',
            'NSEI': '^NSEI',
            'SENSEX': '^BSESN',
            'BSE': '^BSESN',
            'BSESN': '^BSESN',
            'NIFTYBANK': '^NSEBANK',
            'BANKNIFTY': '^NSEBANK',
            'NIFTY BANK': '^NSEBANK'
        }
        
        # Check if it's a known Indian index
        if symbol_upper in indian_indices:
            return indian_indices[symbol_upper], f"💡 Using '{indian_indices[symbol_upper]}' for {symbol}"
        
        return symbol_upper, None
    
    @staticmethod
    def fetch_ROARSTAR(symbol: str, timeframe: str, date: str, time_str: str, count: int) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Fetch ROARSTAR data for a stock.
        
        Args:
            symbol: Stock symbol
            timeframe: One of 'Hourly', 'Daily', 'Weekly', 'Monthly'
            date: Reference date (YYYY-MM-DD)
            time_str: Reference time (HH:MM) - only used for Hourly
            count: Number of previous completed candles to fetch
        
        Returns:
            Tuple of (DataFrame or None, error_message or None)
        """
        try:
            if timeframe not in TIMEFRAMES:
                return None, "❌ Invalid timeframe selected"
            
            # Validate and correct symbol
            corrected_symbol, suggestion = DataFetcher.validate_and_suggest_symbol(symbol)
            
            interval, base_period = TIMEFRAMES[timeframe]
            
            # Extended periods for when more data is needed
            extended_periods = {
                "Hourly": ["7d", "30d", "60d", "90d", "1y"],
                "Daily": ["3mo", "6mo", "1y", "2y", "5y"],
                "Weekly": ["1y", "2y", "5y", "10y", "max"],
                "Monthly": ["3y", "5y", "10y", "15y", "max"]
            }
            
            # Try fetching with progressively longer periods until we get enough candles
            periods_to_try = extended_periods.get(timeframe, [base_period])
            
            # Start from base period and extend if needed
            if base_period not in periods_to_try:
                periods_to_try.insert(0, base_period)
            
            df_filtered = None
            last_error = None
            
            # Create reference datetime (timezone-naive)
            if timeframe == "Hourly":
                ref_datetime = pd.to_datetime(f"{date} {time_str}")
            else:
                ref_datetime = pd.to_datetime(date)
            
            # Check if reference date is in the future
            if ref_datetime > pd.Timestamp.now():
                return None, f"❌ Reference date/time is in the future. Please select a past date."
            
            for period in periods_to_try:
                try:
                    # Fetch data from yfinance
                    ticker = yf.Ticker(corrected_symbol)
                    df = ticker.history(period=period, interval=interval)
                    
                    if df.empty:
                        continue
                    
                    # Remove timezone information from index to avoid comparison issues
                    if df.index.tz is not None:
                        df.index = df.index.tz_localize(None)
                    
                    # Filter: only previous completed candles (exclude current/incomplete)
                    df_filtered = df[df.index < ref_datetime]
                    
                    if df_filtered.empty:
                        continue
                    
                    # Check if we have enough candles
                    if len(df_filtered) >= count:
                        break
                        
                except Exception as e:
                    last_error = str(e)
                    continue
            
            if df_filtered is None or df_filtered.empty:
                # Provide helpful suggestions
                suggestions = []
                if 'NIFTY' in symbol.upper():
                    suggestions.append("💡 For NIFTY 50 index, try: ^NSEI")
                if 'SENSEX' in symbol.upper() or 'BSE' in symbol.upper():
                    suggestions.append("💡 For Sensex, try: ^BSESN")
                if not symbol.endswith('.NS') and not symbol.startswith('^') and len(symbol) > 0:
                    suggestions.append(f"💡 For Indian stocks, try: {symbol}.NS")
                
                error_msg = f"❌ No data available for symbol '{symbol}' with {timeframe} timeframe."
                if suggestions:
                    error_msg += "\n\n" + "\n".join(suggestions)
                else:
                    error_msg += " Please check if the symbol is correct."
                
                return None, error_msg
            
            # Get last 'count' candles and sort chronologically (oldest first, then newer)
            # This shows the oldest previous candle first, then newer ones
            result = df_filtered.tail(count).sort_index(ascending=True)
            
            # Check if we got fewer candles than requested (even after extending period)
            if len(result) < count:
                warning_msg = f"⚠️ Only {len(result)} candles available (requested {count}). Maximum available data fetched."
                return result[['Open', 'High', 'Low', 'Close']], warning_msg
            
            # Return data with suggestion if symbol was corrected
            return result[['Open', 'High', 'Low', 'Close']], suggestion
            
        except Exception as e:
            error_msg = str(e)
            if "No data found" in error_msg or "symbol" in error_msg.lower():
                return None, f"❌ Invalid stock symbol '{symbol}' or symbol not found. Please check the symbol."
            return None, f"❌ Error fetching data: {error_msg}"


def export_to_csv(df: pd.DataFrame, symbol: str, timeframe: str, running_avg_series: pd.Series = None, running_stddev_series: pd.Series = None) -> str:
    """Export DataFrame to CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{timeframe}_{timestamp}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)
    
    # Prepare data for export
    export_df = df.copy()
    export_df.insert(0, 'Period', export_df.index)
    
    # Add Running Average (Open) column if provided (rolling window of 20 rows)
    if running_avg_series is not None:
        # Map running average values based on index
        running_avg_dict = running_avg_series.to_dict()
        export_df['Running Average (Open)'] = export_df.index.map(running_avg_dict)
    
    # Add Running STDDEV.S (Open) column if provided (rolling window of 20 rows)
    if running_stddev_series is not None:
        # Map running STDDEV.S values based on index (NaN will be preserved in CSV for first 19 rows)
        running_stddev_dict = running_stddev_series.to_dict()
        export_df['Running STDDEV.S (Open)'] = export_df.index.map(running_stddev_dict)
    
    # Calculate UB × 2.8, UB × 2.1, UB*1.4, UB*.7, UB*.35, LB*2.8, LB*2.1, LB*1.4, LB*.7, and LB*.35 = Average ± (STDDEV.S × multiplier) for CSV export
    if running_avg_series is not None and running_stddev_series is not None:
        running_avg_dict = running_avg_series.to_dict()
        running_stddev_dict = running_stddev_series.to_dict()
        
        def calculate_ub_2_8_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg + (stddev * 2.8)
        
        def calculate_ub_2_1_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg + (stddev * 2.1)
        
        def calculate_ub_1_4_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg + (stddev * 1.4)
        
        def calculate_ub_0_7_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg + (stddev * 0.7)
        
        def calculate_ub_0_35_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg + (stddev * 0.35)
        
        def calculate_lb_2_8_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg - (stddev * 2.8)
        
        def calculate_lb_2_1_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg - (stddev * 2.1)
        
        def calculate_lb_1_4_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg - (stddev * 1.4)
        
        def calculate_lb_0_7_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg - (stddev * 0.7)
        
        def calculate_lb_0_35_csv(idx):
            avg = running_avg_dict.get(idx)
            stddev = running_stddev_dict.get(idx)
            if pd.isna(avg) or pd.isna(stddev) or avg is None or stddev is None:
                return None
            return avg - (stddev * 0.35)
        
        export_df['UB × 2.8'] = export_df.index.map(calculate_ub_2_8_csv)
        export_df['UB × 2.1'] = export_df.index.map(calculate_ub_2_1_csv)
        export_df['UB*1.4'] = export_df.index.map(calculate_ub_1_4_csv)
        export_df['UB*.7'] = export_df.index.map(calculate_ub_0_7_csv)
        export_df['UB*.35'] = export_df.index.map(calculate_ub_0_35_csv)
        export_df['LB*2.8'] = export_df.index.map(calculate_lb_2_8_csv)
        export_df['LB*2.1'] = export_df.index.map(calculate_lb_2_1_csv)
        export_df['LB*1.4'] = export_df.index.map(calculate_lb_1_4_csv)
        export_df['LB*.7'] = export_df.index.map(calculate_lb_0_7_csv)
        export_df['LB*.35'] = export_df.index.map(calculate_lb_0_35_csv)
    
    export_df.to_csv(filepath, index=False)
    
    return filepath


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Roarstar Stock Analysis Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load settings
    settings = DashboardSettings.load_settings()
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stButton>button {
        width: 100%;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-header">📊 Roarstar Stock Analysis Admin Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("Stock Analysis")
        st.markdown("---")
        
        # Timeframe Selection
        st.subheader("⏱️ Timeframe")
        timeframe = st.radio(
            "Select Timeframe:",
            options=["Hourly", "Daily", "Weekly", "Monthly"],
            index=1,  # Default to Daily
            key="timeframe_selector"
        )
        
        st.markdown("---")
        
        # Settings
        st.subheader("⚙️ Settings")
        
        # Theme Toggle (Streamlit has built-in theme support)
        theme_info = st.info("💡 Use Streamlit's menu (☰) → Settings → Theme to change theme")
        
        # Auto-refresh Toggle
        auto_refresh = st.checkbox(
            "🔄 Auto Refresh",
            value=settings.get("auto_refresh", False),
            help="Automatically refresh data every 10 seconds"
        )
        
        # Save auto-refresh setting
        if auto_refresh != settings.get("auto_refresh", False):
            settings["auto_refresh"] = auto_refresh
            DashboardSettings.save_settings(settings)
        
        st.markdown("---")
        
        # Random Number Feature Section
        st.subheader("🎲 Random Number Feature")
        
        # Initialize session state for random number feature
        if 'random_feature_enabled' not in st.session_state:
            st.session_state.random_feature_enabled = False
        if 'random_t161' not in st.session_state:
            st.session_state.random_t161 = None
        if 'random_t162' not in st.session_state:
            st.session_state.random_t162 = None
        if 'random_locked' not in st.session_state:
            st.session_state.random_locked = False
        
        # Enable/Disable toggle
        random_enabled = st.checkbox(
            "Enable Random Number Column",
            value=st.session_state.random_feature_enabled,
            help="Enable or disable the random number column feature"
        )
        
        # Update session state
        if random_enabled != st.session_state.random_feature_enabled:
            st.session_state.random_feature_enabled = random_enabled
            if not random_enabled:
                # Reset locked state when disabled
                st.session_state.random_locked = False
        
        if 'random_padding_enabled' not in st.session_state:
            st.session_state.random_padding_enabled = False
        if 'random_padding_count' not in st.session_state:
            st.session_state.random_padding_count = 20
        
        if random_enabled:
            st.checkbox(
                "Use Random Numbers For Padding",
                value=st.session_state.random_padding_enabled,
                help="When fewer than 20 forward Open values exist, pad with Random Number values for Average/STDDEV.S",
                key="random_padding_enabled"
            )
            st.number_input(
                "Random Padding Count",
                value=int(st.session_state.random_padding_count),
                min_value=0,
                step=1,
                help="How many Random Number values are available for padding when data is short",
                key="random_padding_count"
            )
        
        # Show input fields only if enabled
        if random_enabled:
            # Check if values are locked
            if st.session_state.random_locked:
                st.success("✅ Random Number Settings Locked")
                st.info(f"**T161:** {st.session_state.random_t161}\n\n**T162:** {st.session_state.random_t162}")
                
                # Show status message
                if 'current_data' in st.session_state and st.session_state['current_data'] is not None:
                    st.success("🎲 Random Number column is active in the data table!")
                else:
                    st.warning("⚠️ Fetch data to see the Random Number column")
                
                # Unlock button
                if st.button("🔓 Unlock Settings", use_container_width=True):
                    st.session_state.random_locked = False
                    st.rerun()
            else:
                # Input fields for T161 and T162
                t161 = st.number_input(
                    "T161",
                    value=float(st.session_state.random_t161) if st.session_state.random_t161 is not None else 100.0,
                    step=0.01,
                    format="%.2f",
                    help="Upper bound for random number calculation"
                )
                
                t162 = st.number_input(
                    "T162",
                    value=float(st.session_state.random_t162) if st.session_state.random_t162 is not None else 0.0,
                    step=0.01,
                    format="%.2f",
                    help="Lower bound for random number calculation"
                )
                
                # Validate T161 > T162
                if t161 <= t162:
                    st.warning("⚠️ T161 must be greater than T162")
                
                # Save/Submit/Done button
                col_save1, col_save2 = st.columns(2)
                with col_save1:
                    if st.button("💾 Save & Lock", use_container_width=True, disabled=(t161 <= t162)):
                        if t161 > t162:
                            st.session_state.random_t161 = t161
                            st.session_state.random_t162 = t162
                            st.session_state.random_locked = True
                            st.success("✅ Settings saved and locked!")
                            st.rerun()
                with col_save2:
                    if st.button("🔄 Reset", use_container_width=True):
                        st.session_state.random_t161 = None
                        st.session_state.random_t162 = None
                        st.session_state.random_locked = False
                        st.rerun()
        
        st.markdown("---")
        
        # Info
        st.info("""
        **Instructions:**
        1. Enter stock symbol
        2. Select reference date/time
        3. Set number of candles
        4. Click 'Fetch Data'
        """)
    
    # Main Content Area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📈 Stock Data Input")
        
        # Input Form
        with st.form("stock_input_form"):
            # Symbol selection with predefined options
            symbol_option = st.selectbox(
                "Select Stock Symbol (or type custom)",
                options=["Custom"] + list(PREDEFINED_SYMBOLS.keys()),
                index=0,
                help="Choose from predefined symbols or select 'Custom' to enter manually"
            )
            
            if symbol_option == "Custom":
                symbol = st.text_input(
                    "Stock Symbol",
                    value="AAPL",
                    placeholder="e.g., AAPL, MSFT, GOOGL, ^NSEI",
                    help="Enter the stock ticker symbol"
                ).upper()
            else:
                # Use predefined symbol
                symbol = PREDEFINED_SYMBOLS[symbol_option]
                st.info(f"📊 Selected: {symbol_option} → {symbol}")
            
            col_date, col_time = st.columns(2)
            
            with col_date:
                ref_date = st.date_input(
                    "Reference Date",
                    value=date.today(),
                    help="Date to use as reference (only previous candles will be fetched)"
                )
            
            with col_time:
                if timeframe == "Hourly":
                    # Quick time selection
                    time_option = st.selectbox(
                        "Quick Time Selection",
                        options=["Custom"] + list(PREDEFINED_TIMES.keys()),
                        index=0,
                        help="Select a predefined time slot or choose 'Custom' for manual entry"
                    )
                    
                    if time_option == "Custom":
                        ref_time = st.time_input(
                            "Reference Time",
                            value=dt_time(9, 15),
                            help="Time to use as reference (Hourly only)"
                        )
                    else:
                        ref_time = PREDEFINED_TIMES[time_option]
                        st.info(f"⏰ Selected: {time_option}")
                else:
                    ref_time = dt_time(0, 0)
                    st.text_input(
                        "Reference Time",
                        value="N/A (Date only)",
                        disabled=True,
                        help="Time is only used for Hourly timeframe"
                    )
            
            count = st.number_input(
                "Number of Candles",
                min_value=1,
                max_value=500,
                value=10,
                step=1,
                help="Number of previous completed candles to fetch"
            )
            
            fetch_button = st.form_submit_button("🚀 Fetch Data", use_container_width=True)
    
    with col2:
        st.header("ℹ️ Current Settings")
        st.markdown(f"**Symbol:** {symbol}")
        st.markdown(f"**Timeframe:** {timeframe}")
        st.markdown(f"**Reference Date:** {ref_date.strftime('%Y-%m-%d')}")
        if timeframe == "Hourly":
            st.markdown(f"**Reference Time:** {ref_time.strftime('%H:%M')}")
        st.markdown(f"**Candle Count:** {count}")
        st.markdown(f"**Auto Refresh:** {'🟢 ON' if auto_refresh else '🔴 OFF'}")
    
    # Fetch and Display Data
    if fetch_button:
        if symbol:
            with st.spinner(f"Fetching {timeframe} data for {symbol}..."):
                date_str = ref_date.strftime("%Y-%m-%d")
                time_str = ref_time.strftime("%H:%M")
                
                data, error_msg = DataFetcher.fetch_ROARSTAR(symbol, timeframe, date_str, time_str, count)
                
                if data is not None and not data.empty:
                    st.session_state['current_data'] = data
                    st.session_state['current_symbol'] = symbol
                    st.session_state['current_timeframe'] = timeframe
                    st.session_state['last_refresh'] = datetime.now()
                    
                    # Show info if symbol was corrected or warning if fewer candles
                    if error_msg:
                        if error_msg.startswith("💡"):
                            st.info(error_msg)
                        else:
                            st.warning(error_msg)
                    
                    st.success(f"✅ Successfully fetched {len(data)} candles!")
                else:
                    # Show specific error message (may contain multiple lines)
                    if error_msg:
                        # Split multi-line error messages
                        error_lines = error_msg.split('\n')
                        for line in error_lines:
                            if line.strip():
                                if line.startswith("💡"):
                                    st.info(line)
                                else:
                                    st.error(line)
                    else:
                        st.error("❌ Failed to fetch data. Please check the symbol and date.")
                    if 'current_data' in st.session_state:
                        del st.session_state['current_data']
        else:
            st.warning("⚠️ Please enter a stock symbol.")
    
    # Auto-refresh indicator
    if auto_refresh and 'last_refresh' in st.session_state:
        time_since_refresh = (datetime.now() - st.session_state['last_refresh']).total_seconds()
        if time_since_refresh < 10:
            st.info(f"🔄 Auto-refresh enabled. Next refresh in {10 - int(time_since_refresh)} seconds...")
        
        # Auto-refresh logic using Streamlit's rerun
        if time_since_refresh >= 10 and 'current_symbol' in st.session_state:
            # Store current form values in session state for auto-refresh
            if 'auto_refresh_symbol' not in st.session_state:
                st.session_state['auto_refresh_symbol'] = symbol
                st.session_state['auto_refresh_timeframe'] = timeframe
                st.session_state['auto_refresh_date'] = ref_date
                st.session_state['auto_refresh_time'] = ref_time
                st.session_state['auto_refresh_count'] = count
            
            # Use stored values for auto-refresh
            refresh_symbol = st.session_state.get('auto_refresh_symbol', symbol)
            refresh_timeframe = st.session_state.get('auto_refresh_timeframe', timeframe)
            refresh_date = st.session_state.get('auto_refresh_date', ref_date)
            refresh_time = st.session_state.get('auto_refresh_time', ref_time)
            refresh_count = st.session_state.get('auto_refresh_count', count)
            
            date_str = refresh_date.strftime("%Y-%m-%d")
            time_str = refresh_time.strftime("%H:%M")
            
            data, error_msg = DataFetcher.fetch_ROARSTAR(
                refresh_symbol,
                refresh_timeframe,
                date_str,
                time_str,
                refresh_count
            )
            
            if data is not None and not data.empty:
                st.session_state['current_data'] = data
                st.session_state['last_refresh'] = datetime.now()
            else:
                # Store error for display (but don't spam during auto-refresh)
                if error_msg:
                    st.session_state['last_error'] = error_msg
            
            # Rerun to update display
            st.rerun()
    
    # Display Data Table
    if 'current_data' in st.session_state and st.session_state['current_data'] is not None:
        data = st.session_state['current_data']
        
        # Determine currency symbol (INR for Indian stocks, USD for others)
        current_symbol = st.session_state.get('current_symbol', '')
        is_indian_stock = current_symbol.endswith('.NS') or current_symbol.startswith('^')
        currency_symbol = '₹' if is_indian_stock else '$'
        
        st.markdown("---")
        st.header("📊 ROARSTAR Data Table")
        
        # Show Random Number Feature status
        if (st.session_state.get('random_feature_enabled', False) and 
            st.session_state.get('random_locked', False) and
            st.session_state.get('random_t161') is not None and
            st.session_state.get('random_t162') is not None):
            st.success(f"🎲 **Random Number Column Active** | T161: {st.session_state.random_t161} | T162: {st.session_state.random_t162}")
        elif st.session_state.get('random_feature_enabled', False):
            st.info("ℹ️ **Random Number Feature:** Enabled but not locked. Go to sidebar to enter T161/T162 and click 'Save & Lock' to activate the column.")
        
        # Add info about trading days
        st.info("ℹ️ **Note:** Only trading days (Monday-Friday) are shown. Weekends and holidays are automatically excluded by the data source.")
        
        # Prepare display dataframe (data is already sorted - oldest previous candle first)
        display_df = data.copy()
        # Ensure order: oldest previous candle first, then newer ones
        display_df = display_df.sort_index(ascending=True)
        
        # Preserve Period (datetime index) before resetting index
        period_series = display_df.index.copy()
        
        # Reset index to add row numbers
        display_df = display_df.reset_index(drop=True)
        
        # Insert No and Period columns
        display_df.insert(0, 'No', range(1, len(display_df) + 1))
        display_df.insert(1, 'Period', period_series)
        
        # Ensure Period is datetime type for proper formatting
        display_df['Period'] = pd.to_datetime(display_df['Period'])
        
        # Add day of week column for clarity
        display_df['Day'] = display_df['Period'].dt.day_name()
        
        # Format numeric columns with currency and thousand separators for better readability
        def format_currency(value):
            """Format number with currency symbol and thousand separators"""
            return f"{currency_symbol}{value:,.2f}"
        
        # Store original numeric values for statistics
        numeric_data = data.copy()
        
        # Calculate Running Average (Open) using forward-looking rolling window of 20 rows
        # Works for all timeframes: Hourly, Daily, Weekly, Monthly
        # First, ensure data is in chronological order (oldest first) for correct rolling calculation
        numeric_data_sorted = numeric_data.sort_index(ascending=True)
        
        random_padding_active = (st.session_state.get('random_feature_enabled', False) and 
                                 st.session_state.get('random_locked', False) and
                                 st.session_state.get('random_padding_enabled', False) and
                                 st.session_state.get('random_t161') is not None and
                                 st.session_state.get('random_t162') is not None)
        if random_padding_active:
            t161 = st.session_state.random_t161
            t162 = st.session_state.random_t162
            pad_count = int(st.session_state.get('random_padding_count', 20))
            random_padding_values = [random.random() * (t161 - t162) + t162 for _ in range(pad_count)]
        else:
            random_padding_values = None
        
        # Calculate rolling average with forward-looking window: Row 1 uses rows 1-20, Row 2 uses rows 2-21, etc.
        # Pandas rolling is backward-looking by default (row 20 = avg of rows 1-20)
        # To make it forward-looking (row 1 = avg of rows 1-20), we shift the result backward by 19 positions
        # This ensures:
        # Row 1: average of rows 1-20 (first 20 Open values)
        # Row 2: average of rows 2-21 (Open values from row 2 to row 21, excluding row 1)
        # Row 3: average of rows 3-22 (Open values from row 3 to row 22, excluding rows 1-2)
        # Rows that don't have 20 forward values will be NaN
        rolling_avg_backward = numeric_data_sorted['Open'].rolling(window=20, min_periods=20).mean()
        # Shift backward by 19 positions: value at row 20 moves to row 1, value at row 21 moves to row 2, etc.
        running_avg = rolling_avg_backward.shift(periods=-19)
        
        # Calculate forward-looking rolling STDDEV.S: Row 1 uses rows 1-20, Row 2 uses rows 2-21, etc.
        # Same forward-looking logic as average
        # Row 1: STDDEV of rows 1-20 (first 20 Open values)
        # Row 2: STDDEV of rows 2-21 (Open values from row 2 to row 21, excluding row 1)
        # Row 3: STDDEV of rows 3-22 (Open values from row 3 to row 22, excluding rows 1-2)
        # Rows that don't have 20 forward values will be NaN
        # ddof=1 ensures sample standard deviation (n-1 in denominator) like Excel STDEV.S
        rolling_stddev_backward = numeric_data_sorted['Open'].rolling(window=20, min_periods=20).std(ddof=1)
        # Shift backward by 19 positions: value at row 20 moves to row 1, value at row 21 moves to row 2, etc.
        running_stddev = rolling_stddev_backward.shift(periods=-19)
        
        if random_padding_values is not None:
            open_series = numeric_data_sorted['Open']
            avg_list = running_avg.tolist()
            std_list = running_stddev.tolist()
            for i in range(len(open_series)):
                if pd.isna(avg_list[i]) or pd.isna(std_list[i]):
                    window_values = open_series.iloc[i:i+20].tolist()
                    if len(window_values) < 20:
                        pad_n = 20 - len(window_values)
                        pad_vals = random_padding_values[:pad_n]
                        window_values.extend(pad_vals)
                    if len(window_values) == 20:
                        s = pd.Series(window_values)
                        avg_list[i] = float(s.mean())
                        std_list[i] = float(s.std(ddof=1))
            running_avg = pd.Series(avg_list, index=numeric_data_sorted.index)
            running_stddev = pd.Series(std_list, index=numeric_data_sorted.index)
        
        # Map running average and STDDEV back to display_df order (oldest first for display)
        # Create mappings from index to values
        running_avg_dict = running_avg.to_dict()
        running_stddev_dict = running_stddev.to_dict()
        
        # Add Running Average (Open) column - map values based on Period index
        display_df['Running Average (Open)'] = display_df['Period'].map(running_avg_dict)
        
        # Add Running STDDEV.S (Open) column - map values based on Period index
        display_df['Running STDDEV.S (Open)'] = display_df['Period'].map(running_stddev_dict)
        
        # Calculate UB × 2.8 = Average + (STDDEV.S × 2.8)
        # Excel equivalent: =F22 + G22 * 2.8
        # Store numeric values before formatting for calculation
        running_avg_numeric = display_df['Running Average (Open)'].copy()
        running_stddev_numeric = display_df['Running STDDEV.S (Open)'].copy()
        
        # Calculate UB × 2.8 row-wise: Average + (STDDEV.S × 2.8)
        def calculate_ub_2_8(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg + (stddev * 2.8)
        
        display_df['UB × 2.8'] = [calculate_ub_2_8(avg, stddev) 
                                   for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate UB × 2.1 row-wise: Average + (STDDEV.S × 2.1)
        # Excel equivalent: =F22 + G22 * 2.1
        def calculate_ub_2_1(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg + (stddev * 2.1)
        
        display_df['UB × 2.1'] = [calculate_ub_2_1(avg, stddev) 
                                   for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate UB*1.4 row-wise: Average + (STDDEV.S × 1.4)
        # Excel equivalent: =F22 + G22 * 1.4
        def calculate_ub_1_4(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg + (stddev * 1.4)
        
        display_df['UB*1.4'] = [calculate_ub_1_4(avg, stddev) 
                                for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate UB*.7 row-wise: Average + (STDDEV.S × 0.7)
        # Excel equivalent: =F22 + G22 * 0.7
        def calculate_ub_0_7(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg + (stddev * 0.7)
        
        display_df['UB*.7'] = [calculate_ub_0_7(avg, stddev) 
                               for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate UB*.35 row-wise: Average + (STDDEV.S × 0.35)
        # Excel equivalent: =F22 + G22 * 0.35
        def calculate_ub_0_35(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg + (stddev * 0.35)
        
        display_df['UB*.35'] = [calculate_ub_0_35(avg, stddev) 
                                for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate LB*2.8 row-wise: Average - (STDDEV.S × 2.8)
        # Excel equivalent: =F22 - G22 * 2.8
        def calculate_lb_2_8(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg - (stddev * 2.8)
        
        display_df['LB*2.8'] = [calculate_lb_2_8(avg, stddev) 
                                for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate LB*2.1 row-wise: Average - (STDDEV.S × 2.1)
        # Excel equivalent: =F22 - G22 * 2.1
        def calculate_lb_2_1(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg - (stddev * 2.1)
        
        display_df['LB*2.1'] = [calculate_lb_2_1(avg, stddev) 
                                for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate LB*1.4 row-wise: Average - (STDDEV.S × 1.4)
        # Excel equivalent: =F22 - G22 * 1.4
        def calculate_lb_1_4(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg - (stddev * 1.4)
        
        display_df['LB*1.4'] = [calculate_lb_1_4(avg, stddev) 
                                for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate LB*.7 row-wise: Average - (STDDEV.S × 0.7)
        # Excel equivalent: =F22 - G22 * 0.7
        def calculate_lb_0_7(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg - (stddev * 0.7)
        
        display_df['LB*.7'] = [calculate_lb_0_7(avg, stddev) 
                               for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Calculate LB*.35 row-wise: Average - (STDDEV.S × 0.35)
        # Excel equivalent: =F22 - G22 * 0.35
        def calculate_lb_0_35(avg, stddev):
            if pd.isna(avg) or pd.isna(stddev):
                return None  # Return None if either value is missing
            return avg - (stddev * 0.35)
        
        display_df['LB*.35'] = [calculate_lb_0_35(avg, stddev) 
                                for avg, stddev in zip(running_avg_numeric, running_stddev_numeric)]
        
        # Format display values
        display_df['Open'] = display_df['Open'].apply(format_currency)
        display_df['High'] = display_df['High'].apply(format_currency)
        display_df['Low'] = display_df['Low'].apply(format_currency)
        display_df['Close'] = display_df['Close'].apply(format_currency)
        
        random_feature_active = (
            st.session_state.get('random_feature_enabled', False) and
            st.session_state.get('random_locked', False) and
            st.session_state.get('random_t161') is not None and
            st.session_state.get('random_t162') is not None
        )
        
        if random_feature_active:
            t161 = st.session_state.random_t161
            t162 = st.session_state.random_t162
            def calculate_random_number():
                return random.random() * (t161 - t162) + t162
            display_df['Random Number'] = [calculate_random_number() for _ in range(len(display_df))]
            display_df['Random Number'] = display_df['Random Number'].apply(format_currency)
        
        # Format Running Average (Open) - handle NaN (show blank)
        # Rows that don't have 20 forward values will be NaN (first rows and last 19 rows)
        def format_running_avg(value):
            if pd.isna(value):
                return "—"  # Show blank/dash for NaN (need 20 forward rows to calculate)
            return format_currency(value)
        
        display_df['Running Average (Open)'] = display_df['Running Average (Open)'].apply(format_running_avg)
        
        # Format Running STDDEV.S (Open) - handle NaN (show blank)
        # Rows that don't have 20 forward values will be NaN (first rows and last 19 rows)
        def format_stddev(value):
            if pd.isna(value):
                return "—"  # Show blank/dash for NaN (need 20 forward rows to calculate)
            return format_currency(value)
        
        display_df['Running STDDEV.S (Open)'] = display_df['Running STDDEV.S (Open)'].apply(format_stddev)
        
        # Format UB × 2.8 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_ub_2_8(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['UB × 2.8'] = display_df['UB × 2.8'].apply(format_ub_2_8)
        
        # Format UB × 2.1 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_ub_2_1(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['UB × 2.1'] = display_df['UB × 2.1'].apply(format_ub_2_1)
        
        # Format UB*1.4 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_ub_1_4(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['UB*1.4'] = display_df['UB*1.4'].apply(format_ub_1_4)
        
        # Format UB*.7 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_ub_0_7(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['UB*.7'] = display_df['UB*.7'].apply(format_ub_0_7)
        
        # Format UB*.35 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_ub_0_35(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['UB*.35'] = display_df['UB*.35'].apply(format_ub_0_35)
        
        # Format LB*2.8 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_lb_2_8(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['LB*2.8'] = display_df['LB*2.8'].apply(format_lb_2_8)
        
        # Format LB*2.1 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_lb_2_1(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['LB*2.1'] = display_df['LB*2.1'].apply(format_lb_2_1)
        
        # Format LB*1.4 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_lb_1_4(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['LB*1.4'] = display_df['LB*1.4'].apply(format_lb_1_4)
        
        # Format LB*.7 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_lb_0_7(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['LB*.7'] = display_df['LB*.7'].apply(format_lb_0_7)
        
        # Format LB*.35 - handle None/NaN (show blank if Average or STDDEV.S is missing)
        def format_lb_0_35(value):
            if pd.isna(value) or value is None:
                return "—"  # Show blank/dash if calculation not possible
            return format_currency(value)
        
        display_df['LB*.35'] = display_df['LB*.35'].apply(format_lb_0_35)
        
        # Reorder columns: No, Period, Day, Open, High, Low, Close, [Random Number if enabled], Running Average (Open), Running STDDEV.S (Open), UB × 2.8, UB × 2.1, UB*1.4, UB*.7, UB*.35, LB*2.8, LB*2.1, LB*1.4, LB*.7, LB*.35
        cols = ['No', 'Period', 'Day', 'Open', 'High', 'Low', 'Close']
        
        # Add Random Number column if it exists (feature enabled and locked)
        if 'Random Number' in display_df.columns:
            cols.append('Random Number')
        
        cols.extend(['Running Average (Open)', 'Running STDDEV.S (Open)', 'UB × 2.8', 'UB × 2.1', 'UB*1.4', 'UB*.7', 'UB*.35', 'LB*2.8', 'LB*2.1', 'LB*1.4', 'LB*.7', 'LB*.35'])
        display_df = display_df[cols]
        
        # Build column configuration dynamically
        column_config = {
            "No": st.column_config.NumberColumn(
                "No",
                width="small",
                format="%d"
            ),
            "Period": st.column_config.DatetimeColumn(
                "Period",
                format="YYYY-MM-DD HH:mm:ss",
                width="medium"
            ),
            "Day": st.column_config.TextColumn(
                "Day",
                width="small",
                help="Day of the week (weekends are automatically excluded)"
            ),
            "Open": st.column_config.TextColumn(
                "Open",
                width="medium",
                help="Opening price"
            ),
            "High": st.column_config.TextColumn(
                "High",
                width="medium",
                help="Highest price"
            ),
            "Low": st.column_config.TextColumn(
                "Low",
                width="medium",
                help="Lowest price"
            ),
            "Close": st.column_config.TextColumn(
                "Close",
                width="medium",
                help="Closing price"
            )
        }
        
        # Add Random Number column config if it exists (insert after Close)
        if 'Random Number' in display_df.columns:
            column_config["Random Number"] = st.column_config.TextColumn(
                "Random Number",
                width="medium",
                help="Random number calculated using formula: random.random() * (T161 - T162) + T162. Only shown when Random Number Feature is enabled and locked."
            )
        
        # Add remaining columns
        column_config.update({
            "Running Average (Open)": st.column_config.TextColumn(
                "Running Average (Open)",
                width="medium",
                help="Forward-looking rolling average of 20 Open prices (Row 1: avg of rows 1-20, Row 2: avg of rows 2-21, Row 3: avg of rows 3-22, etc.). Rows without 20 forward values show blank. Works for all timeframes: Hourly, Daily, Weekly, Monthly."
            ),
            "Running STDDEV.S (Open)": st.column_config.TextColumn(
                "Running STDDEV.S (Open)",
                width="medium",
                help="Forward-looking rolling sample standard deviation of 20 Open prices (Row 1: stddev of rows 1-20, Row 2: stddev of rows 2-21, Row 3: stddev of rows 3-22, etc.). Rows without 20 forward values show blank. Works for all timeframes: Hourly, Daily, Weekly, Monthly."
            ),
            "UB × 2.8": st.column_config.TextColumn(
                "UB × 2.8",
                width="medium",
                help="Upper Band calculated as Average + (Standard Deviation × 2.8). Excel equivalent: =F22+G22*2.8. Shows blank if Average or STDDEV.S is missing."
            ),
            "UB × 2.1": st.column_config.TextColumn(
                "UB × 2.1",
                width="medium",
                help="Upper Band calculated as Average + (Standard Deviation × 2.1). Excel equivalent: =F22+G22*2.1. Shows blank if Average or STDDEV.S is missing."
            ),
            "UB*1.4": st.column_config.TextColumn(
                "UB*1.4",
                width="medium",
                help="Upper Band calculated as Average + (Standard Deviation × 1.4). Excel equivalent: =F22+G22*1.4. Shows blank if Average or STDDEV.S is missing."
            ),
            "UB*.7": st.column_config.TextColumn(
                "UB*.7",
                width="medium",
                help="Upper Band calculated as Average + (Standard Deviation × 0.7). Excel equivalent: =F22+G22*0.7. Shows blank if Average or STDDEV.S is missing."
            ),
            "UB*.35": st.column_config.TextColumn(
                "UB*.35",
                width="medium",
                help="Upper Band calculated as Average + (Standard Deviation × 0.35). Excel equivalent: =F22+G22*0.35. Shows blank if Average or STDDEV.S is missing."
            ),
            "LB*2.8": st.column_config.TextColumn(
                "LB*2.8",
                width="medium",
                help="Lower Band calculated as Average - (Standard Deviation × 2.8). Excel equivalent: =F22-G22*2.8. Shows blank if Average or STDDEV.S is missing."
            ),
            "LB*2.1": st.column_config.TextColumn(
                "LB*2.1",
                width="medium",
                help="Lower Band calculated as Average - (Standard Deviation × 2.1). Excel equivalent: =F22-G22*2.1. Shows blank if Average or STDDEV.S is missing."
            ),
            "LB*1.4": st.column_config.TextColumn(
                "LB*1.4",
                width="medium",
                help="Lower Band calculated as Average - (Standard Deviation × 1.4). Excel equivalent: =F22-G22*1.4. Shows blank if Average or STDDEV.S is missing."
            ),
            "LB*.7": st.column_config.TextColumn(
                "LB*.7",
                width="medium",
                help="Lower Band calculated as Average - (Standard Deviation × 0.7). Excel equivalent: =F22-G22*0.7. Shows blank if Average or STDDEV.S is missing."
            ),
            "LB*.35": st.column_config.TextColumn(
                "LB*.35",
                width="medium",
                help="Lower Band calculated as Average - (Standard Deviation × 0.35). Excel equivalent: =F22-G22*0.35. Shows blank if Average or STDDEV.S is missing."
            )
        })
        
        # Display table with enhanced formatting and column configuration
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
        
        # Statistics
        st.subheader("📈 Statistics")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Average Open", f"{currency_symbol}{numeric_data['Open'].mean():,.2f}")
        with stat_col2:
            st.metric("Average High", f"{currency_symbol}{numeric_data['High'].mean():,.2f}")
        with stat_col3:
            st.metric("Average Low", f"{currency_symbol}{numeric_data['Low'].mean():,.2f}")
        with stat_col4:
            st.metric("Average Close", f"{currency_symbol}{numeric_data['Close'].mean():,.2f}")
        
        # CSV Export
        st.markdown("---")
        st.subheader("💾 Export Data")
        
        col_export1, col_export2 = st.columns([3, 1])
        
        with col_export1:
            st.info(f"Ready to export {len(data)} rows of ROARSTAR data")
        
        with col_export2:
            if st.button("📥 Export to CSV", use_container_width=True):
                # Calculate Running Average (Open) and Running STDDEV.S (Open) for CSV export (forward-looking rolling window of 20 rows)
                # Ensure chronological order for correct rolling calculation
                numeric_data_sorted = numeric_data.sort_index(ascending=True)
                # Calculate backward-looking rolling, then shift to make it forward-looking
                rolling_avg_backward = numeric_data_sorted['Open'].rolling(window=20, min_periods=20).mean()
                running_avg_series = rolling_avg_backward.shift(periods=-19)  # Shift to make forward-looking
                rolling_stddev_backward = numeric_data_sorted['Open'].rolling(window=20, min_periods=20).std(ddof=1)
                running_stddev_series = rolling_stddev_backward.shift(periods=-19)  # Shift to make forward-looking
                random_padding_active = (st.session_state.get('random_feature_enabled', False) and 
                                         st.session_state.get('random_locked', False) and
                                         st.session_state.get('random_padding_enabled', False) and
                                         st.session_state.get('random_t161') is not None and
                                         st.session_state.get('random_t162') is not None)
                if random_padding_active:
                    t161 = st.session_state.random_t161
                    t162 = st.session_state.random_t162
                    pad_count = int(st.session_state.get('random_padding_count', 20))
                    random_padding_values_export = [random.random() * (t161 - t162) + t162 for _ in range(pad_count)]
                    open_series = numeric_data_sorted['Open']
                    avg_list = running_avg_series.tolist()
                    std_list = running_stddev_series.tolist()
                    for i in range(len(open_series)):
                        if pd.isna(avg_list[i]) or pd.isna(std_list[i]):
                            window_values = open_series.iloc[i:i+20].tolist()
                            if len(window_values) < 20:
                                pad_n = 20 - len(window_values)
                                pad_vals = random_padding_values_export[:pad_n]
                                window_values.extend(pad_vals)
                            if len(window_values) == 20:
                                s = pd.Series(window_values)
                                avg_list[i] = float(s.mean())
                                std_list[i] = float(s.std(ddof=1))
                    running_avg_series = pd.Series(avg_list, index=numeric_data_sorted.index)
                    running_stddev_series = pd.Series(std_list, index=numeric_data_sorted.index)
                filepath = export_to_csv(
                    data,
                    st.session_state.get('current_symbol', 'STOCK'),
                    st.session_state.get('current_timeframe', 'Daily'),
                    running_avg_series=running_avg_series,
                    running_stddev_series=running_stddev_series
                )
                st.success(f"✅ Data exported to: `{filepath}`")
                st.download_button(
                    label="⬇️ Download CSV",
                    data=pd.read_csv(filepath).to_csv(index=False),
                    file_name=os.path.basename(filepath),
                    mime="text/csv"
                )
    
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; padding: 1rem;'>"
        "Roarstar Stock Analysis | Professional Trading-Grade Candle Analysis"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
