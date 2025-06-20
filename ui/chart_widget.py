from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import plotly.graph_objects as go
import json
import os
import tempfile
import plotly.utils
import sys

class ChartWidget(QWidget):
    """
    A widget that displays a Plotly chart using QWebEngineView.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = go.Figure()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view for Plotly
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        # Set initial empty figure
        self.update_figure()
    
    def update_figure(self, figure=None):
        """
        Update the displayed figure
        
        Args:
            figure (plotly.graph_objs.Figure, optional): New figure to display. 
                If None, uses current figure.
        """
        if figure is not None:
            self.figure = figure
        
        # Update layout with default styling if no layout is set
        if not self.figure.layout:
            self.figure.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor='#1e1e1e',
                plot_bgcolor='#1e1e1e',
                font=dict(color='white'),
                xaxis=dict(gridcolor='#444'),
                yaxis=dict(gridcolor='#444'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
        
        # Create HTML content with proper string formatting
        html_content = f"""<!DOCTYPE html>
        <html>
            <head>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body, html {{
                        margin: 0;
                        padding: 0;
                        width: 100%;
                        height: 100%;
                        overflow: hidden;
                        background-color: #1e1e1e;
                    }}
                    #plotly-chart {{
                        width: 100%;
                        height: 100%;
                    }}
                    #loading {{
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        color: white;
                        font-family: Arial, sans-serif;
                    }}
                </style>
            </head>
            <body>
                <div id="loading">Loading chart...</div>
                <div id="plotly-chart" style="display: none;"></div>
                <script>
                    function initializePlotly() {{
                        if (typeof Plotly === 'undefined') {{
                            setTimeout(initializePlotly, 100);
                            return;
                        }}
                        
                        document.getElementById('loading').style.display = 'none';
                        document.getElementById('plotly-chart').style.display = 'block';
                        
                        var data = {json.dumps(self.figure.data, cls=plotly.utils.PlotlyJSONEncoder)};
                        var layout = {json.dumps(self.figure.layout, cls=plotly.utils.PlotlyJSONEncoder)};
                        
                        Plotly.newPlot('plotly-chart', data, layout, {{responsive: true}});
                        
                        window.onresize = function() {{
                            Plotly.Plots.resize('plotly-chart');
                        }};
                    }}
                    
                    // Start the initialization
                    document.addEventListener('DOMContentLoaded', initializePlotly);
                    // Also try initializing in case the event has already fired
                    if (document.readyState === 'complete' || document.readyState === 'interactive') {{
                        initializePlotly();
                    }}
                </script>
            </body>
        </html>"""
        
        # Create a temporary HTML file
        temp_file = os.path.join(tempfile.gettempdir(), 'plotly_chart.html')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Load the HTML file in the web view
        self.web_view.setUrl(QUrl.fromLocalFile(temp_file))
    
    def clear_chart(self):
        """Clear the chart"""
        self.figure = go.Figure()
        self.update_figure()
    
    def add_trace(self, trace, row=None, col=None):
        """
        Add a trace to the figure
        
        Args:
            trace: A Plotly trace (e.g., go.Candlestick, go.Scatter)
            row (int, optional): Row position (for subplots)
            col (int, optional): Column position (for subplots)
        """
        if row is not None and col is not None:
            self.figure.add_trace(trace, row=row, col=col)
        else:
            self.figure.add_trace(trace)
        self.update_figure()
    
    def update_layout(self, layout_updates):
        """
        Update the layout of the figure
        
        Args:
            layout_updates (dict): Dictionary of layout updates
        """
        self.figure.update_layout(layout_updates)
        self.update_figure()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Create a sample chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=[1, 3, 2, 4], mode='lines+markers'))
    fig.update_layout(title='Sample Chart')
    
    # Create and show the widget
    widget = ChartWidget()
    widget.setFixedSize(800, 600)
    widget.update_figure(fig)
    widget.show()
    
    sys.exit(app.exec())
