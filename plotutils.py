import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.io import wavfile
from scipy import signal


# For save_spectrogram() → Plotly Heatmap
def create_plotly_spectrogram(filename, nfft=256, noverlap=None):
    """
    Creates a Plotly spectrogram from a WAV file.
    
    Args:
        filename (str): Path to the input .wav file
        nfft (int): The number of data points used in each block for the FFT. 
                   A power 2 is most efficient. Default is 256.
        noverlap (int): The number of points of overlap between blocks. 
                       Default is nfft//2 if nfft <= 128 else 128.
    
    Returns:
        plotly.graph_objects.Figure: Interactive spectrogram figure
    """
    
    # Set default overlap
    if noverlap is None:
        noverlap = nfft // 2 if nfft <= 128 else 128
    
    # Read the WAV file
    try:
        samplerate, data = wavfile.read(filename)
    except Exception as e:
        raise ValueError(f"Error reading WAV file {filename}: {e}")
    
    if len(data.shape) == 1:
        # Create spectrogram using scipy.signal.spectrogram
        frequencies, times, Sxx = signal.spectrogram(
            data, 
            fs=samplerate,
            nperseg=nfft,
            noverlap=noverlap,
            scaling='density'
        )
        
        # Convert to dB scale
        Sxx_db = 10 * np.log10(Sxx + 1e-10)  # Add small value to avoid log(0)
        
        # Create Plotly heatmap
        fig = go.Figure(data=go.Heatmap(
            x=times,
            y=frequencies,
            z=Sxx_db,
            colorscale='Viridis',
            colorbar=dict(title="Power (dB)"),
            hovertemplate='Time: %{x:.2f}s<br>Frequency: %{y:.1f}Hz<br>Power: %{z:.1f}dB<extra></extra>'
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Spectrogram: {filename.split('/')[-1]}",
            xaxis_title="Time (s)",
            yaxis_title="Frequency (Hz)",
            width=800,
            height=500
        )
            
    if len(data.shape) == 2:
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Channel 0', 'Channel 1'),
            vertical_spacing=0.08
        )
        for channel in range(2):
            # Create spectrogram for each channel
            frequencies, times, Sxx = signal.spectrogram(
                data[:, channel], 
                fs=samplerate,
                nperseg=nfft,
                noverlap=noverlap,
                scaling='density'
            )
            
            Sxx_db = 10 * np.log10(Sxx + 1e-10)
            
            # Add heatmap to subplot
            fig.add_trace(
                go.Heatmap(
                    x=times,
                    y=frequencies,
                    z=Sxx_db,
                    colorscale='Viridis',
                    showscale=(channel == 0),  # Only show colorbar for first plot
                    colorbar=dict(title="Power (dB)") if channel == 0 else None,
                    hovertemplate=f'Ch{channel} - Time: %{{x:.2f}}s<br>Frequency: %{{y:.1f}}Hz<br>Power: %{{z:.1f}}dB<extra></extra>'
                ),
                row=channel+1, col=1
            )
        fig.update_layout(
            title=f"Stereo Spectrogram: {filename.split('/')[-1]}",
            height=800,
            width=800
        )
        
        fig.update_xaxes(title_text="Time (s)", row=2, col=1)
        fig.update_yaxes(title_text="Frequency (Hz)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency (Hz)", row=2, col=1)
    
    # Set frequency axis to log scale (optional, comment out for linear)
    # fig.update_yaxes(type="log")
    return fig


# For plot_bb() → Plotly Line Chart  
def create_plotly_bb(bb_df):
    fig = go.Figure(data=go.Scatter(
        x=bb_df.index, 
        y=bb_df.iloc[:, 0],
        mode='lines',
        name='Broadband Level'
    ))
    fig.update_layout(
        title="Broadband Noise Levels",
        xaxis_title="Time",
        yaxis_title="Relative Decibels"
    )
    return fig

def create_plotly_psd(psd_df):
    """
    This function converts a table of power spectral data, having the columns represent frequency bins and the rows
    represent time segments, to a spectrogram.

    Args:
        psd_df: Dataframe of power spectral data.

    Returns: Spectral plot
    """

    fig = go.Figure(
        data=go.Heatmap(x=psd_df.index, y=psd_df.columns, z=psd_df.values.transpose(), colorscale='Viridis',
                        colorbar={"title": 'Magnitude'}))
    fig.update_layout(
        title="Hydrophone Power Spectral Density",
        xaxis_title="Time",
        yaxis_title="Frequency (Hz)",
        legend_title="Magnitude"
    )
    fig.update_yaxes(type="log")
    return(fig)