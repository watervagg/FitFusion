import json
import os
import requests
import time
import datetime

client_id = 'XXXX'
client_secret = 'XXXX'
redirect_uri = 'http://localhost/'

def request_token(client_id, client_secret, code):
    response = requests.post(url='https://www.strava.com/oauth/token',
                             data={'client_id': client_id,
                                   'client_secret': client_secret,
                                   'code': code,
                                   'grant_type': 'authorization_code'})
    return response

def refresh_token(client_id, client_secret, refresh_token):
    response = requests.post(url='https://www.strava.com/api/v3/oauth/token',
                             data={'client_id': client_id,
                                   'client_secret': client_secret,
                                   'grant_type': 'refresh_token',
                                   'refresh_token': refresh_token})
    return response

def write_token(token):
    with open('strava_token.json', 'w') as outfile:
        json.dump(token, outfile)

def get_token():
    with open('strava_token.json', 'r') as token:
        data = json.load(token)
    return data

if not os.path.exists('./strava_token.json'):
    request_url = f'http://www.strava.com/oauth/authorize?client_id={client_id}' \
                  f'&response_type=code&redirect_uri={redirect_uri}' \
                  f'&approval_prompt=force' \
                  f'&scope=profile:read_all,activity:read_all'

    print('Click here:', request_url)
    print('Please authorize the app and copy&paste below the generated code!')
    print('P.S: you can find the code in the URL')
    code = input('Insert the code from the URL: ')

    token = request_token(client_id, client_secret, code)

    # Save json response as a variable
    strava_token = token.json()
    # Save tokens to file
    write_token(strava_token)

data = get_token()

if data['expires_at'] < time.time():
    print('Refreshing token!')
    new_token = refresh_token(client_id, client_secret, data['refresh_token'])
    strava_token = new_token.json()
    # Update the file
    write_token(strava_token)

data = get_token()

access_token = data['access_token']

# Get athlete details
athlete_url = f"https://www.strava.com/api/v3/athlete?" \
              f"access_token={access_token}"
response = requests.get(athlete_url)
athlete = response.json()

# Specify the activity type you want to retrieve
print("Choose the activity type:")
print("1. Running")
print("2. Cycling")
print("3. Swimming")
activity_type_choice = input("Enter the number corresponding to your choice: ")

# Mapping user choice to Strava activity types
activity_types = {
    "1": "Run",
    "2": "Ride",
    "3": "Swim"
}

activity_type_code = activity_types.get(activity_type_choice)
if not activity_type_code:
    print("Invalid choice. Exiting.")
    exit()

# Get activities of the specified type
activities_url = f"https://www.strava.com/api/v3/athlete/activities?" \
                 f"access_token={access_token}"

print('RESTful API:', activities_url)
response = requests.get(activities_url)
activities = response.json()

# Display a list of activities for the selected type (filtering out non-ride activities)
print("="*5, f'{activity_type_code.upper()} ACTIVITIES', "="*5)
filtered_activities = [activity for activity in activities if activity['type'].lower() == activity_type_code.lower()]
for idx, activity in enumerate(filtered_activities, start=1):
    print(f"{idx}. {activity['name']} - {activity['start_date']}")

# Allow the user to select a specific activity
selected_activity_idx = input("Enter the number corresponding to the activity you want to view details: ")

try:
    selected_activity_idx = int(selected_activity_idx)
    selected_activity = filtered_activities[selected_activity_idx - 1]
except (ValueError, IndexError):
    print("Invalid choice. Exiting.")
    exit()
    
# Retrieve and display details for the selected activity
activity_id = selected_activity['id']
activity_url = f"https://www.strava.com/api/v3/activities/{activity_id}?" \
               f"access_token={access_token}"

print('RESTful API:', activity_url)
response = requests.get(activity_url)

if response.status_code == 200:
    activity = response.json()

    # Display details for the selected activity
    print('='*5, 'SELECTED ACTIVITY', '='*5)
    print('Athlete:', athlete['firstname'], athlete['lastname'])
    print('Name:', activity['name'])
    print('Date:', activity['start_date'])
    print('Distance:', round(activity['distance'] / 1000, 2), 'km')  # Convert meters to kilometers
    print('Average Speed:', round(activity['average_speed'] * 3.6, 2), 'km/h')  # Convert m/s to km/h
    print('Max speed:', round(activity['max_speed'] * 3.6, 2), 'km/h')  # Convert m/s to km/h
    print('Average Watts:', round(activity.get('weighted_average_watts', 0), 2))
    print('Max Watts:', round(activity.get('max_watts', 0), 2))
    moving_time_seconds = activity['moving_time']
    moving_time_formatted = str(datetime.timedelta(seconds=moving_time_seconds))
    print('Moving time:', moving_time_formatted)
    if 'location_city' in activity and 'location_state' in activity and 'location_country' in activity:
        print('Location:', activity['location_city'], activity['location_state'], activity['location_country'])
    else:
        print('Location: Unknown')
else:
    print(f"Error retrieving activity details. Status code: {response.status_code}")
    print(response.text)
