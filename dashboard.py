"""
Stock OHLC Analysis Admin Dashboard
A professional web-based admin dashboard for analyzing stock OHLC data using Streamlit.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import json
import os
import time
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
    def fetch_ohlc(symbol: str, timeframe: str, date: str, time_str: str, count: int) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Fetch OHLC data for a stock.
        
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
            
            interval, period = TIMEFRAMES[timeframe]
            
            # Fetch data from yfinance
            ticker = yf.Ticker(corrected_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
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
            
            # Remove timezone information from index to avoid comparison issues
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Create reference datetime (timezone-naive)
            if timeframe == "Hourly":
                ref_datetime = pd.to_datetime(f"{date} {time_str}")
            else:
                ref_datetime = pd.to_datetime(date)
            
            # Check if reference date is in the future
            if ref_datetime > pd.Timestamp.now():
                return None, f"❌ Reference date/time is in the future. Please select a past date."
            
            # Filter: only previous completed candles (exclude current/incomplete)
            df_filtered = df[df.index < ref_datetime]
            
            if df_filtered.empty:
                ref_display = f"{date} {time_str}" if timeframe == "Hourly" else date
                return None, f"❌ No completed candles found before {ref_display}. Try selecting an earlier date/time."
            
            # Get last 'count' candles
            result = df_filtered.tail(count)
            
            # Check if we got fewer candles than requested
            if len(result) < count:
                warning_msg = f"⚠️ Only {len(result)} candles available (requested {count})"
                return result[['Open', 'High', 'Low', 'Close']], warning_msg
            
            # Return data with suggestion if symbol was corrected
            return result[['Open', 'High', 'Low', 'Close']], suggestion
            
        except Exception as e:
            error_msg = str(e)
            if "No data found" in error_msg or "symbol" in error_msg.lower():
                return None, f"❌ Invalid stock symbol '{symbol}' or symbol not found. Please check the symbol."
            return None, f"❌ Error fetching data: {error_msg}"


def export_to_csv(df: pd.DataFrame, symbol: str, timeframe: str) -> str:
    """Export DataFrame to CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{timeframe}_{timestamp}.csv"
    filepath = os.path.join(EXPORTS_DIR, filename)
    
    # Prepare data for export
    export_df = df.copy()
    export_df.insert(0, 'Period', export_df.index)
    export_df.to_csv(filepath, index=False)
    
    return filepath


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Stock OHLC Analysis Dashboard",
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
    st.markdown('<div class="main-header">📊 Stock OHLC Analysis Admin Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("ADMIN DASHBOARD")
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
            symbol = st.text_input(
                "Stock Symbol",
                value="AAPL",
                placeholder="e.g., AAPL, MSFT, GOOGL",
                help="Enter the stock ticker symbol"
            ).upper()
            
            col_date, col_time = st.columns(2)
            
            with col_date:
                ref_date = st.date_input(
                    "Reference Date",
                    value=date.today(),
                    help="Date to use as reference (only previous candles will be fetched)"
                )
            
            with col_time:
                if timeframe == "Hourly":
                    ref_time = st.time_input(
                        "Reference Time",
                        value=dt_time(0, 0),
                        help="Time to use as reference (Hourly only)"
                    )
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
                
                data, error_msg = DataFetcher.fetch_ohlc(symbol, timeframe, date_str, time_str, count)
                
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
            
            data, error_msg = DataFetcher.fetch_ohlc(
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
        
        st.markdown("---")
        st.header("📊 OHLC Data Table")
        
        # Prepare display dataframe
        display_df = data.copy()
        display_df.insert(0, 'No', range(1, len(display_df) + 1))
        display_df.insert(1, 'Period', display_df.index)
        display_df = display_df.reset_index(drop=True)
        
        # Format numeric columns
        display_df['Open'] = display_df['Open'].apply(lambda x: f"{x:.2f}")
        display_df['High'] = display_df['High'].apply(lambda x: f"{x:.2f}")
        display_df['Low'] = display_df['Low'].apply(lambda x: f"{x:.2f}")
        display_df['Close'] = display_df['Close'].apply(lambda x: f"{x:.2f}")
        
        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "No": st.column_config.NumberColumn("No", width="small"),
                "Period": st.column_config.DatetimeColumn("Period", format="YYYY-MM-DD HH:mm:ss"),
                "Open": st.column_config.TextColumn("Open", width="medium"),
                "High": st.column_config.TextColumn("High", width="medium"),
                "Low": st.column_config.TextColumn("Low", width="medium"),
                "Close": st.column_config.TextColumn("Close", width="medium")
            }
        )
        
        # Statistics
        st.subheader("📈 Statistics")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Average Open", f"${data['Open'].mean():.2f}")
        with stat_col2:
            st.metric("Average High", f"${data['High'].mean():.2f}")
        with stat_col3:
            st.metric("Average Low", f"${data['Low'].mean():.2f}")
        with stat_col4:
            st.metric("Average Close", f"${data['Close'].mean():.2f}")
        
        # CSV Export
        st.markdown("---")
        st.subheader("💾 Export Data")
        
        col_export1, col_export2 = st.columns([3, 1])
        
        with col_export1:
            st.info(f"Ready to export {len(data)} rows of OHLC data")
        
        with col_export2:
            if st.button("📥 Export to CSV", use_container_width=True):
                filepath = export_to_csv(
                    data,
                    st.session_state.get('current_symbol', 'STOCK'),
                    st.session_state.get('current_timeframe', 'Daily')
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
        "Stock OHLC Analysis Admin Dashboard | Professional Trading-Grade Candle Analysis"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
