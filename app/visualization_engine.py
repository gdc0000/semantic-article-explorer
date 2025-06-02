# app/visualization_engine.py
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_semantic_map(
    df_display,
    plot_dimensions=2,
    color_by=None,
    symbol_by=None,
    size_by=None,
    hover_name='title',
    hover_data=['id', 'year', 'journal'],
    highlight_indices=None,
    query_point_index=None,
    point_size=5,
    map_height=700
):
    """
    Creates an interactive 2D or 3D semantic map using Plotly Express.

    Args:
        df_display (pd.DataFrame): DataFrame containing 'x', 'y', (optionally 'z'),
                                   and other metadata for plotting.
        plot_dimensions (int): 2 for 2D plot, 3 for 3D plot.
        color_by (str, optional): Column name in df_display to color points by.
        symbol_by (str, optional): Column name for symbol mapping (2D only).
        size_by (str, optional): Column name for point size.
        hover_name (str): Column name for the main hover label.
        hover_data (list): List of column names to show in hover tooltip.
        highlight_indices (list, optional): List of DataFrame indices to highlight as neighbors.
        query_point_index (int, optional): DataFrame index of the query point.
        point_size (int): Default size of the points.
        map_height (int): Height of the plot in pixels.

    Returns:
        plotly.graph_objects.Figure: The Plotly figure object.
    """
    if df_display.empty:
        logging.warning("DataFrame for visualization is empty. Returning empty figure.")
        return go.Figure()

    # Ensure required columns exist
    required_coords = ['x', 'y']
    if plot_dimensions == 3:
        required_coords.append('z')
    if not all(col in df_display.columns for col in required_coords):
        missing = [col for col in required_coords if col not in df_display.columns]
        logging.error(f"Missing coordinate columns for plot: {missing}")
        return go.Figure().update_layout(title_text="Error: Missing coordinate data for plot.")

    # Prepare hover data, ensuring all columns exist
    valid_hover_data = [col for col in hover_data if col in df_display.columns]
    if len(valid_hover_data) != len(hover_data):
        missing_hover = [col for col in hover_data if col not in valid_hover_data]
        logging.warning(f"Missing hover_data columns: {missing_hover}. They will be excluded.")


    # Base plot arguments
    plot_args = {
        'hover_name': hover_name if hover_name in df_display.columns else None,
        'hover_data': {col: True for col in valid_hover_data}, # Show these columns
        'color': color_by if color_by and color_by in df_display.columns else None,
        'height': map_height,
    }
    if size_by and size_by in df_display.columns:
        plot_args['size'] = size_by
        plot_args['size_max'] = point_size * 3 # Example max size for 'size_by'
    else:
        # If not sizing by a column, use a default marker size
        # This is handled differently for 2D and 3D plots
        pass


    # Create a copy for modifications (e.g., adding highlight column)
    df_plot = df_display.copy()
    df_plot['plot_color'] = 'All Documents' # Default category
    df_plot['plot_size'] = point_size # Default size

    if highlight_indices:
        df_plot.loc[highlight_indices, 'plot_color'] = 'Similar Documents'
        df_plot.loc[highlight_indices, 'plot_size'] = point_size * 1.5 # Make neighbors slightly larger
    if query_point_index is not None and query_point_index in df_plot.index:
        df_plot.loc[query_point_index, 'plot_color'] = 'Query/Selected Document'
        df_plot.loc[query_point_index, 'plot_size'] = point_size * 2.0 # Make query point largest

    # Use the new 'plot_color' and 'plot_size' for consistent styling
    plot_args['color'] = 'plot_color'
    # For px.scatter, size is directly specified. For px.scatter_3d, marker.size is used.
    # We will set marker size uniformly later if not using 'size_by'

    color_discrete_map = {
        'All Documents': 'lightblue',
        'Similar Documents': 'orange',
        'Query/Selected Document': 'red'
    }
    if color_by and color_by in df_display.columns and color_by not in ['plot_color', 'plot_size']:
        # If user specified a different color_by, let Plotly handle it,
        # but our highlight logic might override or conflict.
        # For simplicity, we prioritize highlight colors.
        # A more complex setup could combine these.
        logging.info(f"Using 'plot_color' for highlighting. Custom 'color_by={color_by}' might be overridden.")
        plot_args['color_discrete_map'] = color_discrete_map
    else:
        plot_args['color_discrete_map'] = color_discrete_map


    try:
        if plot_dimensions == 3:
            if 'z' not in df_plot.columns:
                logging.error("Z-coordinate missing for 3D plot.")
                return go.Figure().update_layout(title_text="Error: Z-coordinate missing for 3D plot.")
            fig = px.scatter_3d(df_plot, x='x', y='y', z='z', **plot_args)
            # Set uniform marker size if not using 'size_by' column
            if not (size_by and size_by in df_display.columns):
                 fig.update_traces(marker=dict(size=df_plot['plot_size'].tolist())) # Use list for per-point size
            else: # If size_by is used, ensure plot_size doesn't conflict
                 fig.update_traces(marker=dict(sizemode='diameter')) # Or other appropriate sizemode

        else: # 2D plot
            if symbol_by and symbol_by in df_plot.columns:
                plot_args['symbol'] = symbol_by
            fig = px.scatter(df_plot, x='x', y='y', **plot_args)
            # Set uniform marker size if not using 'size_by' column
            if not (size_by and size_by in df_display.columns):
                fig.update_traces(marker=dict(size=df_plot['plot_size'].tolist()))
            else: # If size_by is used
                fig.update_traces(marker=dict(sizemode='diameter'))


        fig.update_layout(
            margin=dict(l=0, r=0, b=0, t=30),
            legend_title_text='Category' if plot_args['color'] == 'plot_color' else (color_by if color_by else ''),
            clickmode='event+select' # Enable click events
        )
        # Make points opaque
        fig.update_traces(marker=dict(opacity=0.8))

        logging.info(f"Successfully created {plot_dimensions}D semantic map.")
        return fig

    except Exception as e:
        logging.error(f"Error creating Plotly figure: {e}")
        st.error(f"Error creating plot: {e}")
        return go.Figure().update_layout(title_text=f"Error generating plot: {e}")

# Example usage (conceptual)
# df = pd.DataFrame({
#     'id': [1, 2, 3, 4, 5],
#     'title': ['A', 'B', 'C', 'D', 'E'],
#     'year': [2020, 2021, 2020, 2022, 2021],
#     'journal': ['J1', 'J2', 'J1', 'J3', 'J2'],
#     'x': [0.1, 0.5, 0.9, 0.3, 0.7],
#     'y': [0.2, 0.6, 0.1, 0.8, 0.4],
#     'z': [0.3, 0.1, 0.7, 0.5, 0.9] # for 3D
# })
# fig = create_semantic_map(df, plot_dimensions=2, highlight_indices=[1,3], query_point_index=0)
# fig.show()