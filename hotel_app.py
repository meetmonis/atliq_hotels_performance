import streamlit as st
import hotel_analysis  
import streamlit_shadcn_ui as ui
import pandas as pd

# Set page config for the app (title, icon, and layout)
st.set_page_config(page_title='Atliq Hospitality', page_icon="📊", layout="wide")

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)



# Header with logo and title
st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px;">
        <h2 style="margin-bottom: -30px; font-size: 36px;">AtliQ Hotels Performance</h2>
        <img src="https://i.postimg.cc/Hs3j8x5Q/logo.png" style="height: 120px; width: 120px; margin-left: 20px;" />
    </div>
""", unsafe_allow_html=True)


# Sidebar filters for user input
st.sidebar.header("Filters")
selected_month = st.sidebar.radio('Select Month', ['All'] + list(hotel_analysis.df_dates['mmm_yy'].dropna().unique()), index=0)
selected_room_type = st.sidebar.selectbox('Select Room Type', ['All'] + list(hotel_analysis.df_rooms['room_class'].unique()), index=0)
selected_city = st.sidebar.selectbox('Select City', ['All'] + list(hotel_analysis.df_hotels['city'].unique()), index=0)
selected_hotel = st.sidebar.selectbox('Select Hotel', ['All'] + list(hotel_analysis.df_hotels['property_name'].unique()), index=0)


# Additional sidebar information
st.sidebar.caption('RevPAR -> Revenue Per Available Room')
st.sidebar.caption('DSRN -> Daily Sellable Room Nights')
st.sidebar.caption('ADR -> Average Daily Rate')
st.sidebar.caption('DURN -> Daily Utilized Room Nights')
st.sidebar.caption('DBRN -> Daily Booking Rate Per Night')


# LinkedIn avatar in the bottom-right corner (Link to profile)
st.markdown("""
    <div class="avatar-container" style="position: fixed; bottom: 20px; right: 20px;">
        <a href="https://www.linkedin.com/in/meetmonis/" target="_blank">
            <img src="https://i.postimg.cc/nh84RRwd/unnamed.jpg" style="border-radius: 50%; height: 40px; width: 40px;">
        </a>
    </div>
""", unsafe_allow_html=True)

# Tab navigation (tabs for different views)
selected_tab = ui.tabs(
    options=['Performance View', 'Booking Insights'], 
    default_value='Performance View', 
)

# Apply filters to the data (based on the selected sidebar options)
filtered_bookings = hotel_analysis.df_merged_bookings.copy()
filtered_agg_bookings = hotel_analysis.df_merged_agg_bookings.copy()
merged_bookings = hotel_analysis.merged_bookings.copy()
bookings = hotel_analysis.merged_bookings.copy()
city_bookings = hotel_analysis.merged_bookings.copy()

# Filter by Room Type if selected
if selected_room_type != 'All':
    filtered_bookings = filtered_bookings[filtered_bookings['room_class'] == selected_room_type]
    filtered_agg_bookings = filtered_agg_bookings[filtered_agg_bookings['room_class'] == selected_room_type]
    merged_bookings = merged_bookings[merged_bookings['room_class'] == selected_room_type]
    bookings = bookings[bookings['room_class'] == selected_room_type]
    city_bookings = city_bookings[city_bookings['room_class'] == selected_room_type]

# Filter by Hotel if selected
if selected_hotel != 'All':
    filtered_bookings = filtered_bookings[filtered_bookings['property_name'] == selected_hotel]
    filtered_agg_bookings = filtered_agg_bookings[filtered_agg_bookings['property_name'] == selected_hotel]
    bookings = bookings[bookings['property_name'] == selected_hotel]
    city_bookings = city_bookings[city_bookings['property_name'] == selected_hotel]
    
# Filter by City if selected
if selected_city != 'All':
    filtered_bookings = filtered_bookings[filtered_bookings['city'] == selected_city]
    filtered_agg_bookings = filtered_agg_bookings[filtered_agg_bookings['city'] == selected_city]
    merged_bookings = merged_bookings[merged_bookings['city'] == selected_city]
    bookings = bookings[bookings['city'] == selected_city]

# Filter by Month if selected
if selected_month != 'All':
    filtered_bookings = filtered_bookings[filtered_bookings['mmm_yy'] == selected_month]
    filtered_agg_bookings = filtered_agg_bookings[filtered_agg_bookings['mmm_yy'] == selected_month]
    merged_bookings = merged_bookings[merged_bookings['mmm_yy'] == selected_month]
    bookings = bookings[bookings['mmm_yy'] == selected_month]
    city_bookings = city_bookings[city_bookings['mmm_yy'] == selected_month]



# Performance View Tab page
# Calculate the filtered Metrics (revenue, occupancy percentage, RevPAR) 
revenue = hotel_analysis.total_revenue(filtered_bookings)
occupancy_per = hotel_analysis.occupancy_percentage(filtered_agg_bookings) 
revpar_value = hotel_analysis.revpar(filtered_bookings, filtered_agg_bookings)
revenue_description = hotel_analysis.revenue_description(filtered_bookings)
occupancy_description = hotel_analysis.occupancy_description(filtered_agg_bookings)
revpar_description = hotel_analysis.revpar_description(filtered_bookings, filtered_agg_bookings)
total_bookings = hotel_analysis.total_bookings(filtered_bookings)
bookings_description = hotel_analysis.bookings_description(filtered_bookings)
adr_value = hotel_analysis.adr(filtered_bookings)
adr_description = hotel_analysis.adr_description(filtered_bookings)
dsrn_value = hotel_analysis.dsrn(bookings)
dsrn_description = hotel_analysis.dsrn_description(bookings)

# Create a hotel performance table 
hotel_performance = merged_bookings.groupby('property_name').agg(
    Revenue=('revenue_realized', 'sum'),
    Bookings=('booking_id', 'count'),
    Capacity=('capacity', 'sum')
).reset_index()

# Convert check-in date to datetime and calculate the date range
merged_bookings['check_in_date'] = pd.to_datetime(merged_bookings['check_in_date'])
date_range = (merged_bookings['check_in_date'].max() - merged_bookings['check_in_date'].min()).days + 1

hotel_performance['Occupancy %'] = hotel_performance['Bookings'] / hotel_performance['Capacity']
hotel_performance['cancellation %'] = merged_bookings[merged_bookings.booking_status == 'Cancelled'].shape[0] / merged_bookings.booking_id.count()
hotel_performance['Realization %'] = (1 - ((merged_bookings[merged_bookings.booking_status == 'Cancelled'].shape[0] + 
                                              merged_bookings[merged_bookings.booking_status == 'No Show'].shape[0]) / merged_bookings.shape[0]))
hotel_performance['ADR'] = hotel_performance['Revenue'] / hotel_performance['Bookings']
hotel_performance['RevPAR'] = hotel_performance['Revenue'] / hotel_performance['Capacity'] 
hotel_performance['DSRN'] = hotel_performance['Capacity'] / date_range
hotel_performance['DBRN'] = hotel_performance['Bookings'] / date_range
hotel_performance['DURN'] = merged_bookings[merged_bookings.booking_status == 'Checked Out'].shape[0] / date_range
hotel_performance['Average Rating'] = merged_bookings['ratings_given'].mean()

hotel_performance['Revenue'] = hotel_performance['Revenue'].apply(hotel_analysis.format_number)
hotel_performance['Bookings'] = hotel_performance['Bookings'].apply(hotel_analysis.format_number)
hotel_performance['Capacity'] = hotel_performance['Capacity'].apply(hotel_analysis.format_number)
hotel_performance['Occupancy %'] = hotel_performance['Occupancy %'].apply(lambda x: f"{round(x * 100, 1)}%")
hotel_performance['cancellation %'] = hotel_performance['cancellation %'].apply(lambda x: f"{round(x * 100, 1)}%")
hotel_performance['Realization %'] = hotel_performance['Realization %'].apply(lambda x: f"{round(x * 100, 1)}%")
hotel_performance['ADR'] = hotel_performance['ADR'].apply(hotel_analysis.format_number)
hotel_performance['RevPAR'] = hotel_performance['RevPAR'].apply(hotel_analysis.format_number)
hotel_performance['DSRN'] = hotel_performance['DSRN'].apply(hotel_analysis.format_number)
hotel_performance['DBRN'] = hotel_performance['DBRN'].apply(hotel_analysis.format_number)
hotel_performance['DURN'] = hotel_performance['DURN'].apply(hotel_analysis.format_number)
hotel_performance['Average Rating'] = hotel_performance['Average Rating'].apply(lambda x: f"{round(x, 1)}")

hotel_performance.rename(columns={'property_name': 'Property Name'}, inplace=True)
hotel_performance = hotel_performance[['Property Name', 'Revenue', 'Bookings', 'Capacity', 'Occupancy %', 'cancellation %', 'Realization %', 
                                       'ADR', 'RevPAR', 'DSRN', 'DBRN', 'DURN', 'Average Rating']]

# Display content based on the selected tab
if selected_tab == 'Performance View':
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="Total Revenue", content=revenue, description=revenue_description, key="card1")
    with cols[1]:
        ui.metric_card(title="Occupancy %", content=occupancy_per, description=occupancy_description, key="card2")
    with cols[2]:
        ui.metric_card(title="RevPAR", content=revpar_value, description=revpar_description, key="card3")
    
    columns_table = st.columns(1)
    with columns_table[0]:
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; width: 100%;">
         <h5 style="font-size: 15px; margin-bottom: -10px; text-align: center;">Insights By Property</h5>
          </div>
        """, unsafe_allow_html=True)
        st.dataframe(hotel_performance)
    
    col1, col2 = st.columns(2)
    with col1:
        fig = hotel_analysis.revenue_pie_chart(merged_bookings)
        st.plotly_chart(fig)
    with col2:
        fig = hotel_analysis.realization_per_adr(bookings)
        st.plotly_chart(fig)

elif selected_tab == 'Booking Insights':
    cols = st.columns(3)
    with cols[0]:
        ui.metric_card(title="Total Bookings", content=total_bookings, description=bookings_description, key="card1")
    with cols[1]:
        ui.metric_card(title="ADR", content=adr_value, description=adr_description, key="card2")
    with cols[2]:
        ui.metric_card(title="DSRN", content=dsrn_value, description=dsrn_description, key="card3")

    col = st.columns(2)
    with col[0]:
        fig = hotel_analysis.occ_line(bookings)
        st.plotly_chart(fig) 
    with col[1]:
        fig = hotel_analysis.booking_percentage_by_platform(bookings)
        st.plotly_chart(fig)
        
    colum = st.columns(3)
    with colum[0]:
        fig = hotel_analysis.adr_pie_chart(bookings)
        st.plotly_chart(fig)
    with colum[1]:
        fig = hotel_analysis.room_class_by_occ(bookings)
        st.plotly_chart(fig)
    with colum[2]:
        fig = hotel_analysis.bar_city(city_bookings)
        st.plotly_chart(fig)
    