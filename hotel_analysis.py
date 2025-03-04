import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load cleaned data
df_bookings = pd.read_csv('cleaned datasets/fact_bookings.csv')
df_dates = pd.read_csv('cleaned datasets/dim_date.csv')
df_hotels = pd.read_csv('cleaned datasets/dim_hotels.csv')
df_rooms = pd.read_csv('cleaned datasets/dim_room.csv')
df_aggregated_bookings = pd.read_csv('cleaned datasets/fact_aggregated_bookings.csv')
merged_bookings = pd.read_csv('cleaned datasets/merged_bookings_data.csv')

# Format values for easier readability
def format_number(value):
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:.0f}"

# Convert date in datetime format for easier manipulation
df_dates['date'] = pd.to_datetime(df_dates['date'])

# Merging bookings data
df_merged_bookings = df_bookings.merge(df_rooms, left_on='room_category', right_on='room_id', how='left')
df_merged_bookings = df_merged_bookings.merge(df_hotels, left_on='property_id', right_on='property_id', how='left')
df_merged_bookings['check_in_date'] = pd.to_datetime(df_merged_bookings['check_in_date'], format='%d-%b-%y')
df_merged_bookings = df_merged_bookings.merge(df_dates, left_on='check_in_date', right_on='date', how='left')

# Merging aggregated bookings data
df_merged_agg_bookings = df_aggregated_bookings.merge(df_rooms, left_on='room_category', right_on='room_id', how='left')
df_merged_agg_bookings = df_merged_agg_bookings.merge(df_hotels, left_on='property_id', right_on='property_id', how='left')
df_merged_agg_bookings['check_in_date'] = pd.to_datetime(df_merged_agg_bookings['check_in_date'], format='%d-%b-%y')
df_merged_agg_bookings = df_merged_agg_bookings.merge(df_dates, left_on='check_in_date', right_on='date', how='left')


# KPI Matrics
# Calculate total revenue
def total_revenue(filtered_bookings):
    revenue = filtered_bookings['revenue_realized'].sum()
    return format_number(revenue)

# Calculate occupancy percentage
def occupancy_percentage(filtered_agg_bookings):
    successful_bookings = float(filtered_agg_bookings.successful_bookings.sum())
    capacity = filtered_agg_bookings.capacity.sum()
    occ_per = successful_bookings / capacity
    return f"{round(occ_per * 100, 1)}%"

# Calculate RevPAR (Revenue per Available Room)
def revpar(filtered_bookings, filtered_agg_bookings):
    total_revenue = filtered_bookings['revenue_realized'].sum()
    total_capacity = filtered_agg_bookings['capacity'].sum()
    if total_capacity == 0:
        return format_number(0)
    return format_number(total_revenue / total_capacity)

# Calculate ADR (Average Daily Rate)
def adr(filtered_bookings):
    revenue = filtered_bookings.revenue_realized.sum()
    bookings = filtered_bookings.booking_id.count()
    result = revenue / bookings
    return format_number(result)

# Calculate DSRN (Daily Sellable Room Nights)
def dsrn(bookings):
    bookings['date'] = pd.to_datetime(bookings['date'])
    num_days = (bookings['date'].max() - bookings['date'].min()).days + 1
    return format_number(bookings.capacity.sum() / num_days)

# Calculate total bookings
def total_bookings(filtered_bookings):
    bookings = filtered_bookings.booking_id.count()
    return format_number(bookings)



# Calculate the KPI labels for revenue
def revenue_description(filtered_bookings):
    filtered_bookings = filtered_bookings.copy()
    filtered_bookings.loc[:, 'week_no'] = filtered_bookings['week_no'].astype(str)
    selected_week = filtered_bookings['week_no'].str.extract(r'(\d+)').astype(int).max()[0]
    rev_cw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week}', 'revenue_realized'].sum()
    rev_pw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week - 1}', 'revenue_realized'].sum()
    if rev_pw == 0 or pd.isna(rev_pw):
        return "Revenue vs Last Week: No data for previous week"
    wow_change = ((rev_cw / rev_pw) - 1) * 100
    if wow_change > 0:
        return f"Revenue vs Last Week: ▲ +{wow_change:.1f}%"
    else:
        return f"Revenue vs Last Week: ▼ {wow_change:.1f}%"

# Calculate RevPAR (Revenue per Available Room) comparison
def revpar_description(filtered_bookings, filtered_agg_bookings):
    filtered_bookings = filtered_bookings.copy()
    filtered_agg_bookings = filtered_agg_bookings.copy()
    filtered_bookings.loc[:, 'week_no'] = filtered_bookings['week_no'].astype(str)
    filtered_agg_bookings.loc[:, 'week_no'] = filtered_agg_bookings['week_no'].astype(str)
    selected_week = filtered_bookings['week_no'].str.extract(r'(\d+)').astype(int).max()[0]
    rev_cw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week}', 'revenue_realized'].sum()
    capacity_cw = filtered_agg_bookings.loc[filtered_agg_bookings['week_no'] == f'W {selected_week}', 'capacity'].sum()
    revpar_cw = rev_cw / capacity_cw if capacity_cw != 0 else 0
    selected_week_prev = selected_week - 1
    rev_pw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week_prev}', 'revenue_realized'].sum()
    capacity_pw = filtered_agg_bookings.loc[filtered_agg_bookings['week_no'] == f'W {selected_week_prev}', 'capacity'].sum()
    revpar_pw = rev_pw / capacity_pw if capacity_pw != 0 else 0
    if revpar_pw != 0:
        wow_change = ((revpar_cw - revpar_pw) / revpar_pw) * 100
    else:
        wow_change = 0
    if wow_change > 0:
        return f"RevPAR vs Last Week: ▲  +{wow_change:.1f}%"
    else:
        return f"RevPAR vs Last Week: ▼ {wow_change:.1f}%"

# Calculate average occupancy percentage
def occupancy_description(filtered_agg_bookings):
    filtered_agg_bookings['check_in_date'] = pd.to_datetime(filtered_agg_bookings['check_in_date'], errors='coerce')
    filtered_agg_bookings['week_period'] = filtered_agg_bookings['check_in_date'].dt.to_period('W-SUN')
    successful_bookings = filtered_agg_bookings.groupby('week_period')['successful_bookings'].sum()
    capacity = filtered_agg_bookings.groupby('week_period')['capacity'].sum()
    occupancy_percentage = (successful_bookings / capacity) * 100
    avg_occ = occupancy_percentage.mean()
    return f"Average Occupancy: {avg_occ: .1f}%"

# Calculate the bookings description
def bookings_description(filtered_bookings):
    filtered_bookings = filtered_bookings.copy()
    filtered_bookings.loc[:, 'week_no'] = filtered_bookings['week_no'].astype(str)
    selected_week = filtered_bookings['week_no'].str.extract(r'(\d+)').astype(int).max()[0]
    rev_cw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week}', 'booking_id'].count()
    rev_pw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week - 1}', 'booking_id'].count()
    if rev_pw == 0 or pd.isna(rev_pw):
        return "Total Bookings vs Last Week: No data for previous week"
    wow_change = ((rev_cw / rev_pw) - 1) * 100
    if wow_change > 0:
        return f"Total Bookings vs Last Week: ▲ +{wow_change:.1f}%"
    else:
        return f"Total Bookings vs Last Week: ▼ {wow_change:.1f}%"


# Calculate ADR percentage changes (Weekly comparison)
def adr_description(filtered_bookings):
    filtered_bookings = filtered_bookings.copy()
    filtered_bookings['week_no'] = filtered_bookings['week_no'].astype(str)
    selected_week = filtered_bookings['week_no'].str.extract(r'(\d+)').astype(int).max()[0]
    rev_cw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week}', 'revenue_realized'].sum()
    capacity_cw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week}', 'booking_id'].count()
    revpar_cw = rev_cw / capacity_cw if capacity_cw != 0 else 0
    selected_week_prev = selected_week - 1
    rev_pw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week_prev}', 'revenue_realized'].sum()
    capacity_pw = filtered_bookings.loc[filtered_bookings['week_no'] == f'W {selected_week_prev}', 'booking_id'].count()
    revpar_pw = rev_pw / capacity_pw if capacity_pw != 0 else 0
    if revpar_pw != 0:
        wow_change = ((revpar_cw - revpar_pw) / revpar_pw) * 100
    else:
        wow_change = 0
    if wow_change > 0:
        return f"ADR vs Last Week: ▲  +{wow_change:.1f}%"
    else:
        return f"ADR vs Last Week: ▼  {wow_change:.1f}%"


# Calculate DSRN percentage changes (Weekly comparison)
def dsrn_description(bookings):
    filtered_agg_bookings = bookings.copy()
    filtered_agg_bookings['check_in_date'] = pd.to_datetime(filtered_agg_bookings['check_in_date'])
    num_days = (filtered_agg_bookings['check_in_date'].max() - filtered_agg_bookings['check_in_date'].min()).days + 1
    filtered_agg_bookings['week_no'] = filtered_agg_bookings['week_no'].astype(str)
    selected_week = filtered_agg_bookings['week_no'].str.extract(r'(\d+)').astype(int).max()[0]
    
    rev_cw = filtered_agg_bookings.loc[filtered_agg_bookings['week_no'] == f'W {selected_week}', 'capacity'].sum()
    capacity_cw = filtered_agg_bookings.loc[filtered_agg_bookings['week_no'] == f'W {selected_week}'].shape[0] * num_days
    dsrn_cw = rev_cw / capacity_cw if capacity_cw != 0 else 0
    
    selected_week_prev = selected_week - 1
    rev_pw = filtered_agg_bookings.loc[filtered_agg_bookings['week_no'] == f'W {selected_week_prev}', 'capacity'].sum()
    capacity_pw = filtered_agg_bookings.loc[filtered_agg_bookings['week_no'] == f'W {selected_week_prev}'].shape[0] * num_days
    dsrn_pw = rev_pw / capacity_pw if capacity_pw != 0 else 0
    
    if dsrn_pw != 0:
        wow_change = ((dsrn_cw - dsrn_pw) / dsrn_pw) * 100
    else:
        wow_change = 0
    
    if wow_change > 0:
        return f"DSRN vs Last Week: ▲  +{wow_change:.1f}%"
    else:
        return f"DSRN vs Last Week: ▼ {wow_change:.1f}%"



# Create the charts For the Visualization 
# Revenue % Pie Chart
def revenue_pie_chart(merged_bookings):
    pie_chart_data = merged_bookings.groupby('category')['revenue_realized'].sum().reset_index()
    total_revenue = pie_chart_data['revenue_realized'].sum()
    pie_chart_data['percentage'] = (pie_chart_data['revenue_realized'] / total_revenue) * 100
    labels = pie_chart_data['category']
    values = pie_chart_data['percentage']
    colors = ['#d4d4d4' if i % 2 == 0 else '#2b2b2b' for i in range(len(labels))]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.7,
        textinfo='percent+label',
        hoverinfo='label+percent',
        marker=dict(colors=colors)
    )])
    
    fig.add_annotation(
        text=f"Revenue: {format_number(total_revenue)}",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=15, color='#3b3b3b'),
        align='center'
    )
    
    fig.update_layout(
        title=dict(text='% Revenue by Category', x=0.05, xanchor='left', font=dict(size=13, family='Arial', weight='normal')),
        showlegend=True,
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=1.0,
            yanchor='bottom'
        )
    )

    return fig


# Create combo line or column chart realization% and adr by platform
def realization_per_adr(bookings):
    result = bookings.groupby('booking_platform').agg(
        Revenue=('revenue_realized', 'sum'),
        Bookings=('booking_id', 'count'),
    )
    
    result['ADR'] = result['Revenue'] / result['Bookings']
    
    canceled_or_no_show = bookings[bookings.booking_status.isin(['Cancelled', 'No Show'])]
    canceled_or_no_show_count = canceled_or_no_show.groupby('booking_platform')['booking_id'].count()
    
    realization_percentage = 1 - (canceled_or_no_show_count / bookings.groupby('booking_platform')['booking_id'].count())
    result['Realization %'] = realization_percentage.fillna(0) * 100
    result['ADR'] = result['ADR'].apply(lambda x: f"{round(x / 1000, 1)}K" if x >= 1000 else round(x, 1))
    
    result['Realization %'] = result['Realization %'].apply(lambda x: f"{round(x, 1)}%")
    
    result = result[['ADR', 'Realization %']]

    adr_values = result['ADR'].values
    realization_values = result['Realization %'].apply(lambda x: float(x.replace('%', ''))).values
    x = result.index.tolist()
    
    area_trace = go.Scatter(
        x=x,
        y=adr_values,
        mode="lines+markers",
        name="ADR",
        line=dict(color="#2b2b2b"),
    )
    
    bar_trace = go.Bar(
        x=x,
        y=realization_values,
        name="Realization%",
        marker=dict(color="#a2a2a2"),
        text=result['Realization %'].values,
        textposition="outside",
    )
    
    fig = go.Figure(data=[area_trace, bar_trace])

    fig.update_layout(
        title=dict(text='Realization % & ADR by Platform', x=0.05, xanchor='left', font=dict(size=13, family='Arial', weight='normal')),
        showlegend=True,
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            
        ),
        xaxis=dict(showgrid=False),
        bargap=0.5,
        height=500
    )
    
    return fig


# Occupancy% by week no
def occ_line(bookings):
    result = bookings.groupby('week_no').agg(
        successful_bookings=('successful_bookings', 'sum'),
        capacity=('capacity', 'sum')
    )
    
    result['Occupancy %'] = result['successful_bookings'] / result['capacity']
    
    fig = px.line(result, x=result.index, y='Occupancy %')
    
    fig.update_traces(
        mode='lines+markers',
        line=dict(color='#2b2b2b', width=2),
        marker=dict(size=5, color='#1a1a1a', line=dict(width=2, color='#1a1a1a'))
    )
    
    fig.update_layout(
        title=dict(
            text='Occupancy % by Week Number', 
            x=0.05, 
            xanchor='left', 
            font=dict(size=13, family='Arial', weight='normal')
        ),
        showlegend=False,
        xaxis=dict(
            title='', 
            showticklabels=True
        ),
        yaxis=dict(
            title='',  
            showticklabels=True,
            showgrid=False,
            tickfont=dict(size=10),
            tickformat=".1%"
        )
    )
    
    return fig


# Calculate booking percentage by platform
def booking_percentage_by_platform(bookings):
    platform_counts = bookings['booking_platform'].value_counts()
    total_bookings = bookings['booking_id'].count()
    booking_percentage = (platform_counts / total_bookings) * 100
    booking_percentage = booking_percentage.round(2)
    booking_percentage = booking_percentage.apply(lambda x: f'{x}%')
    
    result = platform_counts.to_frame(name='Platform Counts')
    result['Booking %'] = booking_percentage

    fig = px.bar(result, x=result.index, y='Platform Counts', text='Booking %', labels={
        'x': 'Platform',
        'y': 'Booking %'
    })
    
    fig.update_traces(
        texttemplate='%{text}', 
        textposition='outside', 
        marker_color='#1a1a1a'
    )
    
    fig.update_layout(
        title=dict(text='% Bookings by Platform', x=0.05, xanchor='left', font=dict(size=13, family='Arial', weight='normal')),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
        xaxis=dict(
            showgrid=False, 
            showticklabels=True,  
            tickangle=45 
        ),
        plot_bgcolor='white',
        bargap=0.5,
        xaxis_title='',  
        yaxis_title=''  
    )
    
    fig.update_traces(texttemplate='%{text}', textposition='outside', textfont_size=11)
    
    return fig


# ADR By category
def adr_pie_chart(bookings):
    result = bookings.groupby('category').agg(
        Revenue=('revenue_realized', 'sum'),
        Bookings=('booking_id', 'count'),
    )
    
    result['ADR'] = result['Revenue'] / result['Bookings']
    result['ADR_display'] = result['ADR'].apply(lambda x: f"{round(x / 1000, 1)}K" if x >= 1000 else round(x, 1))
    
    labels = result.index
    values = result['ADR']
    
    colors = ['#d4d4d4' if i % 2 == 0 else '#2b2b2b' for i in range(len(labels))]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.7,
        textinfo='percent+label',
        hoverinfo='label+percent',
        marker=dict(colors=colors)
    )])
    
    overall_adr = result['ADR'].mean()
    fig.add_annotation(
        text=f"ADR: {format_number(overall_adr)}",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=15, color='#3b3b3b'),
        align='center'
    )
    
    fig.update_layout(
        title=dict(text='Adr by Category', x=0.05, xanchor='left', font=dict(size=13, family='Arial', weight='normal')),
        showlegend=True,
        legend=dict(
            orientation='h',
            x=0.5,
            xanchor='center',
            y=1.0,
            yanchor='bottom'
        )
    )

    return fig


# Calculate the funnel chart room class
def room_class_by_occ(bookings):
    result = bookings.groupby('room_class').agg(
        successful_bookings=('successful_bookings', 'sum'),
        capacity=('capacity', 'sum')
    )
    
    result['Occupancy %'] = (result['successful_bookings'] / result['capacity']) * 100
    result = result.sort_values(by='Occupancy %', ascending=False)
    result['Occupancy %'] = result['Occupancy %'].apply(lambda x: f"{x:.1f}%")
    
    occ_values = result['Occupancy %'].tolist()
    room_classes = result.index.tolist()

    df = pd.DataFrame({
        'number': occ_values,
        'stage': ['Occupancy %'] * len(occ_values),
        'room_class': room_classes
    })

    fig = go.Figure(go.Funnel(
        y=df['room_class'],
        x=df['number'],
        textinfo="percent initial", 
        marker=dict(color='#5b5b5b', line=dict(width=0)),
    ))

    fig.update_layout(
        title=dict(text='Occupancy % by Room Class', x=0.05, xanchor='left', font=dict(size=13, family='Arial', weight='normal')),
        showlegend=False,
        xaxis=dict(showticklabels=False),
        yaxis=dict(showticklabels=True, tickfont=dict(color='black')),
    )

    return fig


#calculate the bar chart by booking%
def bar_city(city_bookings):
    platform_counts = city_bookings['city'].value_counts()
    total_bookings = city_bookings['booking_id'].count()
    booking_percentage = (platform_counts / total_bookings) * 100
    booking_percentage = booking_percentage.round(1)
    booking_percentage = booking_percentage.apply(lambda x: f'{x}%')
    
    result = platform_counts.to_frame(name='Platform Counts')
    result['Booking %'] = booking_percentage
    
    result = result.sort_values(by='Platform Counts', ascending=False)
    
    fig = go.Figure(go.Bar(
        x=result['Booking %'],
        y=result.index,
        text=result['Booking %'],
        orientation='h',
        marker_color='rgb(70, 70, 70)'
    ))
    
    fig.update_layout(
        title=dict(text='% Bookings by City', x=0.05, xanchor='left', font=dict(size=13, family='Arial', weight='normal')),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=True),
        xaxis=dict(
            showgrid=False, 
            showticklabels=False,  
            tickangle=45
        ),
        plot_bgcolor='white',
        bargap=0.5,
        xaxis_title='',  
        yaxis_title=''
    )
    
    fig.update_traces(
        texttemplate='%{text}', 
        textposition='inside',
        textfont_size=12
    )
    
    return fig

