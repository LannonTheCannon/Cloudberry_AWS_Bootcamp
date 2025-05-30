# Disclaimer: This function was generated by AI. Please review before using.
# Agent Name: data_visualization_agent
# Time Created: 2025-05-30 01:45:07

def data_visualization(data_raw):
    import pandas as pd
    import numpy as np
    import json
    import plotly.graph_objects as go
    import plotly.io as pio





    # Data is expected as a DataFrame with the given structure
    df = data_raw.copy()

    # Categories in the order given
    categories = df['Category'].tolist()

    # Create box plot traces manually using quartiles and whiskers
    # Plotly box trace can be supplied with q1, median, q3, lowerfence, upperfence, and outliers

    # For each category, prepare the components for box plot
    boxes = []
    for idx, row in df.iterrows():
        category = row['Category']

        q1 = row['25%']
        median = row['50%']
        q3 = row['75%']
        lowerfence = row['min']
        upperfence = row['max']

        # Outliers info: number of outliers and ratio
        outlier_count = int(row['Outlier Count'])
        outlier_ratio = row['Outlier Ratio']

        # To indicate outliers as points, we will place them just outside the whiskers
        # We don't have exact values for outliers, so we simulate some points slightly beyond whiskers
        # Number of outlier points = outlier_count (if > 0)
        # We will spread them evenly just beyond upper whisker for demonstration

        outlier_y = []
        if outlier_count > 0:
            # Place outliers just above upper whisker with small jitter
            jitter = (upperfence - q3) * 0.1 if (upperfence - q3) > 0 else 10
            # Generate outlier points spaced by jitter
            outlier_y = [upperfence + jitter*(i+1) for i in range(outlier_count)]

        # Build a box trace with quartiles and whiskers defined
        box = go.Box(
            name=category,
            q1=[q1],
            median=[median],
            q3=[q3],
            lowerfence=[lowerfence],
            upperfence=[upperfence],
            boxpoints=False,  # hide default points (all points)
            marker=dict(color='blue'),
            line=dict(width=2),
            showlegend=False,
        )
        boxes.append(box)

        # Add scatter trace for outliers if any
        if outlier_y:
            outlier_scatter = go.Scatter(
                x=[category]*len(outlier_y),
                y=outlier_y,
                mode='markers',
                marker=dict(color='red', symbol='circle-open', size=8),
                name=f'{category} Outliers',
                showlegend=True
            )
            boxes.append(outlier_scatter)

    # Compose figure
    fig = go.Figure(data=boxes)

    fig.update_layout(
        title="Distribution of Total Sales per Transaction by Category with Variability and Outliers",
        xaxis_title="Category",
        yaxis_title="Total Sales per Transaction",
        yaxis=dict(zeroline=False),
        boxmode='group',
        template="plotly_white",
        legend=dict(title="Outliers", itemsizing='constant'),
    )

    # Convert figure to dict
    fig_json = pio.to_json(fig)
    fig_dict = json.loads(fig_json)

    return fig_dict