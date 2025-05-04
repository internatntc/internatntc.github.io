# myapp/views.py
import time
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from .firebase_config import db_ref


def add_users_to_towers(request):
    if request.method == "POST":
        # Assuming checkboxes named 'towers'
        selected_towers = request.POST.getlist('towers')
        phone_numbers = request.POST.get(
            'phone_numbers', '').split(',')  # Comma-separated input
        phone_numbers = [num.strip() for num in phone_numbers if num.strip()]

        if not selected_towers or not phone_numbers:
            messages.error(
                request, "Please select at least one tower and enter phone numbers.")
            return render(request, 'map_app/add_users.html')

        try:
            for tower_id in selected_towers:
                tower_ref = db_ref.child(f'user_cells/{tower_id}')
                # Get existing users
                existing_users = tower_ref.get() or {}

                # If existing data is a list (from JS), convert to dict
                if isinstance(existing_users, list):
                    temp = {num: {'towerId': tower_id}
                            for num in existing_users}
                    existing_users = temp

                # Add or update users as objects
                for num in phone_numbers:
                    existing_users[num] = {'towerId': tower_id}

                # Save to Firebase
                tower_ref.set(existing_users)
                print(f"Added users to Tower {tower_id}: {existing_users}")

            messages.success(request, "Users added to towers successfully!")
            return redirect('add_users_to_towers')
        except Exception as e:
            messages.error(request, f"Error adding users: {str(e)}")
            return render(request, 'map_app/add_users.html')

    return render(request, 'map_app/add_users.html')


def send_message(request):
    if request.method == "POST":
        selected_towers = request.POST.getlist('towers')
        message = request.POST.get('message', '').strip()

        if not selected_towers or not message:
            messages.error(
                request, "Please select at least one tower and enter a message.")
            return render(request, 'map_app/send_message.html')

        try:
            users_to_send = set()

            # Fetch users for each tower
            for tower_id in selected_towers:
                tower_ref = db_ref.child(f'user_cells/{tower_id}')
                users_data = tower_ref.get() or {}
                if isinstance(users_data, dict):
                    # Add phone numbers
                    users_to_send.update(users_data.keys())

            if not users_to_send:
                messages.error(
                    request, "No users found for the selected towers.")
                return render(request, 'map_app/send_message.html')

            # Store the message for each user and tower
            for tower_id in selected_towers:
                for user in users_to_send:
                    msg_ref = db_ref.child(
                        f'messages/tower_{tower_id}/user_{user}')
                    msg_ref.set({
                        'message': message,
                        'towerId': tower_id,
                        # Milliseconds like JS
                        'timestamp': int(time.time() * 1000)
                    })

            messages.success(
                request, f"Message sent successfully to {len(users_to_send)} users!")
            return redirect('send_message')
        except Exception as e:
            messages.error(request, f"Error sending message: {str(e)}")
            return render(request, 'map_app/send_message.html')

    return render(request, 'map_app/send_message.html')


def get_message_groups():
    """
    Retrieve and display messages from Firebase, sorted by timestamp globally.

    Fetches all messages from the 'messages' node in the Firebase Realtime Database,
    converts timestamps from milliseconds to datetime objects, and organizes them
    to display the latest message across all towers at the top. Groups identical
    messages sent to multiple towers for a concise display. Renders a standalone
    template extending 'map_app/show_towers.html'.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Renders 'map_app/view_messages.html' with processed messages.

    Context Variables:
        message_groups (list): A list of dictionaries, each representing a unique
            message with its towers, users, and timestamp, sorted by timestamp
            (newest first).
    """
    messages_data = db_ref.child('messages').get() or {}
    all_messages = []

    for tower_id, tower_data in messages_data.items():
        tower_id_clean = tower_id.replace('tower_', '')
        for user_id, msg_data in tower_data.items():
            timestamp_ms = msg_data.get('timestamp')
            timestamp_dt = datetime.fromtimestamp(
                timestamp_ms / 1000) if timestamp_ms else None

            all_messages.append({
                'towerId': tower_id_clean,
                'userId': user_id.replace('user_', ''),
                'message': msg_data.get('message'),
                'timestamp': timestamp_dt
            })

    all_messages.sort(key=lambda x: x['timestamp']
                      or datetime.min, reverse=True)

    message_groups = {}
    for msg in all_messages:
        message_text = msg['message']
        if message_text not in message_groups:
            message_groups[message_text] = {
                'message': message_text,
                'timestamp': msg['timestamp'],
                'towers': {}
            }
        tower_dict = message_groups[message_text]['towers']
        if msg['towerId'] not in tower_dict:
            tower_dict[msg['towerId']] = []
        tower_dict[msg['towerId']].append(msg['userId'])

    message_groups_list = [
        {
            'message': data['message'],
            'timestamp': data['timestamp'],
            'towers': data['towers']
        }
        for data in message_groups.values()
    ]
    message_groups_list.sort(
        key=lambda x: x['timestamp'] or datetime.min, reverse=True)
    return message_groups_list
