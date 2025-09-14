from os.path import join as pjoin 
from pathlib import Path
import glob
import streamlit as st
from plotutils import * 
import pandas as pd
import datetime
from datetime import datetime as dt

# In your Streamlit app:

# hydrophone_name="orcasound_lab"

# Configure page layout
st.set_page_config(
    page_title="Orcasound Shipnoise Analyzer",
    page_icon="🔊",
    layout="wide"
)

def find_files_by_date(location, selected_date, file_extensions=['.wav', '.pickle']):
    """
    Helper function to find all files in subdirectories under a location 
    that start with the given date.
    
    Args:
        location (str): Hydrophone location name
        selected_date (datetime.date): Date to search for
        file_extensions (list): List of file extensions to search for
    
    Returns:
        dict: Dictionary with timestamps as keys and file paths as values
    """
    data_path = Path(f"output/{location}")
    
    # Convert date to the expected filename format: YYYY-MM-DD
    date_str = selected_date.strftime("%Y-%m-%d")
    
    matching_files = {}
    
    if not data_path.exists():
        return matching_files
    
    # Go through all subdirectories
    for subdir in data_path.iterdir():
        if subdir.is_dir():
            # Search in wav subdirectory
            wav_dir = subdir / "wav"
            if wav_dir.exists():
                for ext in file_extensions:
                    pattern = f"{date_str}T*{ext}"
                    files = list(wav_dir.glob(pattern))
                    
                    for file_path in files:
                        # Extract timestamp from filename (without extension)
                        timestamp = file_path.stem
                        if timestamp not in matching_files:
                            matching_files[timestamp] = {}
                        matching_files[timestamp][ext] = str(file_path)
            
            # Also search in pkl subdirectories if they exist
            pkl_dirs = ["pkl/bb", "pkl/psd"]
            for pkl_subdir in pkl_dirs:
                pkl_path = subdir / pkl_subdir
                pkl_type=pkl_subdir.split("/")[1]
                if pkl_path.exists():
                    pattern = f"{date_str}T*.pickle"
                    files = list(pkl_path.glob(pattern))
                    
                    for file_path in files:
                        timestamp = file_path.stem
                        if timestamp not in matching_files:
                            matching_files[timestamp] = {}
                        matching_files[timestamp][pkl_type] = str(file_path)
    
    return matching_files

def filter_timestamps_by_time_range(available_files, start_time, end_time):
    """
    Filter timestamps based on time range.
    
    Args:
        available_files (dict): Dictionary of available files by timestamp
        start_time (datetime.time): Start time filter
        end_time (datetime.time): End time filter
    
    Returns:
        dict: Filtered dictionary of available files
    """
    filtered_files = {}
    
    for timestamp, files in available_files.items():
        try:
            # Parse timestamp format: YYYY-MM-DDTHH-MM-SS-fff
            # Convert to datetime to extract time
            timestamp_dt = dt.strptime(timestamp, "%Y-%m-%dT%H-%M-%S-%f")
            file_time = timestamp_dt.time()
            
            # Check if file time is within the specified range
            if start_time <= end_time:
                # Normal case: start_time < end_time (e.g., 08:00 to 18:00)
                if start_time <= file_time <= end_time:
                    filtered_files[timestamp] = files
            else:
                # Handle overnight range: start_time > end_time (e.g., 22:00 to 06:00)
                if file_time >= start_time or file_time <= end_time:
                    filtered_files[timestamp] = files
                    
        except ValueError:
            # Skip timestamps that don't match expected format
            continue
    
    return filtered_files

def create_sidebar_layout():
    st.title("🔊 Orcasound Shipnoise Analyzer")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("📊 Data Selection")
        
        # Location selection
        st.subheader("🗺️ Location")
        locations = [
            "bush_point", 
            "orcasound_lab", 
            "port_townsend", 
            "sunset_bay", 
            "sandbox"
        ]
        selected_location = st.selectbox(
            "Choose hydrophone location:",
            locations,
            index=1  # Default to orcasound_lab
        )
        
        # Fixed date - representing latest 24 hours (demo data from 2025-09-01)
        selected_date = datetime.date(2025, 9, 1)
        
        # Show current data period
        st.subheader("📅 Data Period")
        st.info(f"Latest 24 Hours: {selected_date.strftime('%Y-%m-%d')}")
        st.caption("Demo data - In production, this would show the most recent 24 hours of data")
        
        # Time range selection
        st.subheader("⏰ Time Range")
        col1, col2 = st.columns(2)
        
        with col1:
            time_start = st.time_input(
                "Start time:",
                value=datetime.time(0, 0),
                help="Filter files from this time"
            )
        
        with col2:
            time_end = st.time_input(
                "End time:",
                value=datetime.time(23, 59),
                help="Filter files until this time"
            )
        
        # Timestamp selection
        st.subheader("🕐 Timestamp")
        
        # Find available files for the selected date and location
        all_available_files = find_files_by_date(selected_location, selected_date)
        
        # Filter files by time range
        available_files = filter_timestamps_by_time_range(all_available_files, time_start, time_end)
        
        if available_files:
            # Sort timestamps chronologically
            sorted_timestamps = sorted(available_files.keys())
            
            selected_timestamp = st.selectbox(
                "Available timestamps:",
                sorted_timestamps,
                help=f"Files found between {time_start.strftime('%H:%M')} and {time_end.strftime('%H:%M')}"
            )
            
            # Show file info
            if selected_timestamp in available_files:
                file_info = available_files[selected_timestamp]
                st.info(f"📁 Available files:")
                for ext, path in file_info.items():
                    file_name = Path(path).name
                    st.text(f"{ext}: {file_name}")
        else:
            if all_available_files:
                st.warning(f"No files found between {time_start.strftime('%H:%M')} and {time_end.strftime('%H:%M')} in {selected_location}")
                st.info(f"Found {len(all_available_files)} files outside the time range")
            else:
                st.warning(f"No files found for {selected_location} in the latest 24 hours")
            selected_timestamp = None
        
        # Action button
        st.markdown("---")
        process_button = st.button(
            "🚀 Generate Graphs",
            type="primary",
            use_container_width=True,
            disabled=not bool(available_files)
        )
    
    # Main content area - spectrogram display
    if process_button and selected_timestamp and available_files:
        # Show selected parameters
        st.info(f"📍 **Location**: {selected_location} | 📅 **Date**: {selected_date} | ⏰ **Time**: {time_start.strftime('%H:%M')} - {time_end.strftime('%H:%M')} | 🕐 **Timestamp**: {selected_timestamp}")
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Get the file paths
            file_info = available_files[selected_timestamp]
            # Check which files are available
            has_wav = '.wav' in file_info
            has_psd = 'psd' in file_info
            has_bb = 'bb' in file_info

            #----------------Spectrogram from unprocessed WAV----------------#
            if not has_wav:
                st.error("No WAV file found for the selected timestamp")
                return
            
            wav_file_path = file_info['.wav']
            
            status_text.text("Loading audio data...")
            progress_bar.progress(33)
            
            # Verify file exists
            if not Path(wav_file_path).exists():
                st.error(f"WAV file not found: {wav_file_path}")
                return
            
            status_text.text("Creating spectrogram...")
            progress_bar.progress(66)
            
            # Create spectrogram using the function we created earlier
            fig_spectrogram = create_plotly_spectrogram(wav_file_path, nfft=256)
            
            status_text.text("Rendering plot...")
            progress_bar.progress(90)
            
            # Display the spectrogram
            st.subheader("📈 Audio Spectrogram (from WAV file)")
            st.write("This spectrogram is generated directly from the raw audio file, showing frequency content over time with basic processing.")
            st.plotly_chart(fig_spectrogram, use_container_width=True)
            
            #----------------PSD Spectrogram----------------#
            # Load and display PSD spectrogram if available
            if has_psd:
                status_text.text("Loading PSD data...")
                progress_bar.progress(60)
                
                try:
                    psd_df = pd.read_pickle(file_info['psd'])
                    fig_psd = create_plotly_psd(psd_df)
                    
                    st.subheader("🔬 Processed Spectrogram (PSD)")
                    st.write("This spectrogram shows processed power spectral density data with advanced filtering and denoising applied, providing a cleaner view of the acoustic signature.")
                    st.plotly_chart(fig_psd, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load PSD data: {e}")
            else:
                st.warning("⚠️ No processed PSD data available for this timestamp")
            
            # Load and display broadband RMS if available
            if has_bb:
                status_text.text("Loading broadband data...")
                progress_bar.progress(80)
                
                try:
                    bb_df = pd.read_pickle(file_info['bb'])
                    fig_bb = create_plotly_bb(bb_df)
                    
                    st.subheader("📊 Broadband Noise Levels")
                    st.write("This time series shows the overall acoustic energy levels across all frequencies, useful for identifying periods of increased ship noise or other acoustic events.")
                    st.plotly_chart(fig_bb, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not load broadband RMS data: {e}")
            else:
                st.warning("⚠️ No broadband RMS data available for this timestamp")
            
            progress_bar.progress(100)
            status_text.text("✅ All graphs generated successfully!")

        except Exception as e:
            st.error(f"Error processing data: {e}")
            st.exception(e)  # Show full error details for debugging
        finally:
            # Clean up progress indicators after a short delay
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
    
    elif not available_files:
        st.info("👈 Please adjust your time range selection from the sidebar")
    else:
        st.info("👈 Please select a timestamp and click 'Generate Graphs' to begin analysis")

# Main app
def main():
    create_sidebar_layout()

if __name__ == "__main__":
    main()