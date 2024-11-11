import socket
import json
from request import Message


def request_playlist(client_socket, client_ip, server_ip):
    """
    Author: Ankita Dewangswami

    :param client_socket: A socket object that connects client to the server. It utilizes socket connection for
    communication.
    :param client_ip: The IP address of the client to identify the sender.
    :param server_ip: The IP address of the server for acknowledgement.
    Sending playlist request: A Message object is created with message_type as 3 and client_ip and server_ip
                              to specify the source and destination
    Receiving the Response: It receives response from the server using client_socket.recv(4096)
    which reads up 4096 bytes of data from the socket.
    Processing the response: The payload is parsed as JSON. If the response contains 'error' key, the error message is printed.
                             If the response contains 'updated_playlist' keu, it prints the details of each song in the playlist.
    Exception handling: If the response does not match with the expected formats, it logs an unexpected response message.
    """

    playlist_request_msg = Message(3, "", client_ip=client_ip, server_ip=server_ip)
    client_socket.sendall(playlist_request_msg.to_bytes())
    print("Sent request for receiving the current playlist.")

    try:

        response_data = client_socket.recv(4096)
        response_msg = Message.from_bytes(response_data)

        print("Received response message from the client:", response_msg)

        """
        The below if conditional statement is for to check the message type. In this client-server architecture,
        the message type '6' is for receiving the updated playlist from the server side after manipulating the playlist.
        Further in the code it checks for the update_playlist if present in the server response received by the client.
        It iterates over the updated_playlist and prints the list of songs from the it.
        """
        if response_msg.message_type == 6:
            print("In the message_type =6 if conditional clause")
            payload = json.loads(response_msg.payload)

            if "error" in payload:
                print(f"Error: {payload['error']}")
            elif "updated_playlist" in payload:
                print("Updated Playlist:")
                for song in payload["updated_playlist"]:
                    print(
                        f"ID: {song['id']}, Title: {song['song_title']}, Artist: {song['artist']}, Album: {song['album_title']}, Duration: {song['duration']}")
            else:
                print("Received unexpected response format from server:", payload)
        else:
            print("Unknown response format from server.")
    except Exception as e:
        print(f"Error receiving response from server: {e}")


def request_catalog(client_socket, client_ip, server_ip):
    """
    The request_catalog function is designed to request a list of songs from a server and handle the response.
    In this method 'Message' object called catalog_request_msg is created and it specifies an empty payload.
    The message is converted to bytes using to_bytes() and sent to the server through client_socket.sendall().

    :param client_socket: A socket object for sending and receiving data.
    :param client_ip: The IP address of the client.
    :param server_ip: The IP address of the server.
    """
    catalog_request_msg = Message(1, "", client_ip=client_ip, server_ip=server_ip)
    client_socket.sendall(catalog_request_msg.to_bytes())
    print("Sent catalog request to the server...")

    try:
        header = client_socket.recv(8)
        if not header:
            print("No response from server...")
            return

        """
        The following code gets the length of the payload from the header and it
        receives the payload based on teh length specified in teh header which later combines the
        header and the payload.
        """
        length = int.from_bytes(header[1:3], 'big')
        payload = client_socket.recv(length)
        full_response = header + payload

        response_msg = Message.from_bytes(full_response)

        if response_msg.message_type == 2:
            if response_msg.payload:
                try:
                    catalog = json.loads(response_msg.payload)
                    print("Received catalog:")
                    for song in catalog:
                        """ Print the details of the song in the catalog by iterating over the catalog json list.
                        """
                        print(
                            f"ID: {song['id']}, Title: {song['song_title']}, Artist: {song['artist']}, Album: {song['album_title']}, Duration: {song['duration']}")
                except json.JSONDecodeError:
                    print("Error decoding JSON response from server.")
                    print(f"Received payload: {response_msg.payload}")
            else:
                print("Received an empty catalog response.")

    except Exception as e:
        print(f"Error receiving catalog response: {e}")


def open_new_playlist(client_socket, client_ip, server_ip):
    new_playlist_msg = Message(7, "", client_ip=client_ip, server_ip=server_ip)
    client_socket.sendall(new_playlist_msg.to_bytes())
    print("Sent request to open a new playlist on the server.")

    """
    It receives the data from the socket and converts the data into structured data format.
    """
    response_data = client_socket.recv(4096)
    response = Message.from_bytes(response_data)

    """
    Conditional check for message type 8 and print the payload associated with that message.
    """
    if response.message_type == 8:
        print("Response from the server side: ", response.payload)
    else:
        print("Unknown response from the server side: ", response.message_type)


def add_song_to_playlist(client_socket, client_ip, server_ip):
    """
    The main purpose of the function is to add the song from the catalog by asking for the desired
    song ID the user wants to add to the playlist.
    The message type 5 indicated that the type for this operation is 5 which represents the 'add song to playlist' action.
    Payload: The song_id is sent as the payload in this message to the server.

    Send the Request to the Server
    The Message object is converted to bytes using the to_bytes() method and sent to the server via the client socket.
    The function prints the confirmation that the song addition request has been sent.

    :param client_socket: A socket object for sending and receiving data.
    :param client_ip: The IP address of the client.
    :param server_ip: The IP address of the server.

    """
    song_id = input("Enter the song ID to add to the playlist: ")
    add_song_msg = Message(5, song_id, client_ip=client_ip, server_ip=server_ip)
    client_socket.sendall(add_song_msg.to_bytes())
    print(f"Requested to add song ID: {song_id} to the playlist.")

    while True:
        try:
            header = client_socket.recv(8)
            if not header:
                print("No response from server.")
                break

            length = int.from_bytes(header[1:3], 'big')
            payload = client_socket.recv(length)
            full_response = header + payload

            response_msg = Message.from_bytes(full_response)
            print("response_msg.message_type:", response_msg.message_type)

            """
            Message type check: The received message type is for receiving updated playlist
            after adding the songs in the active_playlist on the server side.
            Before attempting to process the payload to retrieve the data on the client side, 
            it ensures that the payload is not empty. 
            JSON parsing: It tries to decode the payload from JSON format. There are possible keys it checks for:
            1.Updated playlist: If the updated playlist presents in the message type 6 it prints the update_playlist
             and Error handling: If the key "error" is present, it prints the error message.
            """
            if response_msg.message_type == 6:
                if response_msg.payload:
                    try:
                        received_data = json.loads(response_msg.payload)
                        if "updated_playlist" in received_data:
                            print("Received updated playlist:")
                            for song in received_data["updated_playlist"]:
                                print(
                                    f"ID: {song['id']}, Title: {song['song_title']}, Artist: {song['artist']}, Album: {song['album_title']}, Duration: {song['duration']}")
                        elif "error" in received_data:
                            print(f"Error: {received_data['error']}")

                        else:
                            print("Unknown response format from server.")
                    except json.JSONDecodeError:
                        print("Error decoding JSON response from server.")
                        print(f"Received payload: {response_msg.payload}")
                else:
                    """Empty response check if the payload received from the server is empty."""
                    print("Received an empty response.")
            break

        except Exception as e:
            """This is a broader exception handling mechanism to check if 
            any unexpected error occurred during the response processing."""
            print(f"Error receiving response: {e}")
            break


def remove_song_from_playlist(client_socket, client_ip, server_ip):
    """
    This method manipulated the process of requesting the removal of a song from a playlist on the server.
    Get the song id as input from the client. Send the remove song message request to the server.
    The server response after receiving and processing the data.
    The following if conditional statement handles different response scenarios.
    """
    song_id = input("Enter the song ID to remove from the playlist: ")

    remove_song_msg = Message(9, song_id, client_ip=client_ip,
                              server_ip=server_ip)
    client_socket.sendall(remove_song_msg.to_bytes())
    print(f"Requested to remove song ID: {song_id} from the playlist.")

    try:
        response_data = client_socket.recv(4096)
        response_msg = Message.from_bytes(response_data)
        payload = json.loads(response_msg.payload)

        if "success" in payload:
            print(payload["success"])
            print("Updated Playlist:")
            for song in payload["updated_playlist"]:
                print(
                    f"ID: {song['id']}, Title: {song['song_title']}, Artist: {song['artist']}, Album: {song['album_title']}, Duration: {song['duration']}")
        elif "error" in payload:
            print(f"Error: {payload['error']}")
        else:
            print("Received unexpected response from the server.")
    except Exception as e:
        print(f"Error receiving response from server: {e}")


def find_song_by_id(client_socket, client_ip, server_ip):
    song_id = input("Enter the song ID to find: ").strip()

    if not song_id.isdigit():
        print("Error: Song ID must be a valid number.")
        return

    find_song_msg = Message(10, song_id, client_ip=client_ip,
                            server_ip=server_ip)
    client_socket.sendall(find_song_msg.to_bytes())
    print(f"Sent request to find song ID: {song_id}")

    try:
        response_data = client_socket.recv(4096)
        response_msg = Message.from_bytes(response_data)

        if response_msg.message_type == 11:
            payload = json.loads(response_msg.payload)
            print(
                f"Song found: ID: {payload['id']}, Title: {payload['song_title']}, Artist: {payload['artist']}, Album: {payload['album_title']}, Duration: {payload['duration']}")
        elif response_msg.message_type == 12:
            payload = json.loads(response_msg.payload)
            print(f"Error: {payload['error']}")
        else:
            print("Unknown response format from server.")
    except Exception as e:
        print(f"Error receiving response from server: {e}")


def switch_to_play_mode(client_socket, client_ip, server_ip, mode):
    """
    Send a request to the server to switch to play mode with a specified submode.

    Args:
        client_socket (socket): The client socket to send the message.
        client_ip (str): The client's IP address.
        server_ip (str): The server's IP address.
        mode (str): The submode to apply in play mode (default, shuffle, loop).

    Returns:
        dict: The server response indicating the playlist status.
    """
    payload = json.dumps({"mode": mode})
    play_mode_msg = Message(13, payload, client_ip=client_ip,
                            server_ip=server_ip)
    client_socket.sendall(play_mode_msg.to_bytes())

    response = client_socket.recv(4096)
    print("Raw response received:", response)
    response_msg = Message.from_bytes(response)
    response_data = json.loads(response_msg.payload)

    play_mode = response_data.get('play_mode')
    now_playing = response_data.get('now_playing', {})
    if now_playing:
        print(f"Now playing: {now_playing['song_title']} by {now_playing['artist']}")
    else:
        print("No song is currently playing.")

    print(f"Play mode switched to: {play_mode}")

    # Handle the default mode specifically
    #if play_mode == "default":
    # Print the now playing song

    # Print the current playlist details
    print("Current Playlist:")
    playlist = response_data.get('playlist', [])
    if isinstance(playlist, list) and playlist:
        for song in playlist:
            print(f"ID: {song['id']}, Title: {song['song_title']}, Artist: {song['artist']}, "
                  f"Album: {song['album_title']}, Duration: {song['duration']}")
    else:
        print("The playlist is empty.")
    return response_data


def play_next_song(client_socket, client_ip, server_ip):
    """
    Send a request to the server to play the next song in the playlist.

    Args:
        client_socket (socket): The client socket to send the message.
        client_ip (str): The client's IP address.
        server_ip (str): The server's IP address.

    Returns:
        dict: The server response indicating the next song or an error.
    """
    play_next_msg = Message(14, "", client_ip=client_ip, server_ip=server_ip)
    client_socket.sendall(play_next_msg.to_bytes())

    response = client_socket.recv(4096)
    response_msg = Message.from_bytes(response)
    payload = json.loads(response_msg.payload)
    if 'now_playing' in payload:
        print(f"Now Playing: {payload['now_playing']['song_title']} by {payload['now_playing']['artist']}")
    else:
        print("No more songs in the playlist.")


def go_back(client_socket, client_ip, server_ip):
    """
    Send a request to the server to restore the last dequeued song and move it to the front.

    Args:
        client_socket (socket): The client socket to send the message.
        client_ip (str): The client's IP address.
        server_ip (str): The server's IP address.

    Returns:
        dict: The server response indicating success or failure of the operation.
    """
    go_back_msg = Message(15, "", client_ip=client_ip, server_ip=server_ip)
    client_socket.sendall(go_back_msg.to_bytes())

    response = client_socket.recv(4096)
    response_msg = Message.from_bytes(response)
    return json.loads(response_msg.payload)


def client():
    server_host = 'localhost'
    server_port = 12000

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))

    client_ip = client_socket.getsockname()[0]
    server_ip = client_socket.getpeername()[0]

    print(f"Connected to the server at {server_ip} from {client_ip}.")

    while True:

        print("\nOptions:")
        print("1: Request Catalog")
        print("2: Open New Playlist")
        print("3: Request Current Playlist")
        print("4: Add Song to Playlist")
        print("5: Remove song from playlist")
        print("6: Find song by ID")
        print("7: Switch to Play Mode")
        print("8: Play Next Song")
        print("9: Go Back to Previous Song")
        print("10: Quit")
        choice = input("Enter your choice (1, 2, 3, 4, 5, 6, 7, 8, 9, or 10): ")

        options = {
            '1': lambda: request_catalog(client_socket, client_ip, server_ip),
            '2': lambda: open_new_playlist(client_socket, client_ip, server_ip),
            '3': lambda: request_playlist(client_socket, client_ip, server_ip),
            '4': lambda: add_song_to_playlist(client_socket, client_ip, server_ip),
            '5': lambda: remove_song_from_playlist(client_socket, client_ip, server_ip),
            '6': lambda: find_song_by_id(client_socket, client_ip, server_ip),
            '7': lambda: switch_to_play_mode_option(client_socket, client_ip, server_ip),
            '8': lambda: play_next_song_option(client_socket, client_ip, server_ip),
            '9': lambda: go_back_option(client_socket, client_ip, server_ip),
            '10': lambda: (client_socket.close(), print("Connection closed."), exit())
        }

        action = options.get(choice)
        if action:
            action()
        else:
            print("Invalid option. Please try again.")
    client_socket.close()


def switch_to_play_mode_option(client_socket, client_ip, server_ip):
    print("Choose play mode:")
    print("1: Default")
    print("2: Shuffle")
    print("3: Loop")
    choice = input("Enter your choice (1, 2, or 3): ")

    mode_map = {
        '1': 'default',
        '2': 'shuffle',
        '3': 'loop'
    }

    selected_mode = mode_map.get(choice)
    if selected_mode:
        response = switch_to_play_mode(client_socket, client_ip, server_ip, selected_mode)

        print("Raw server response:", response)

        if "error" in response:
            print(f"Error: {response['error']}")
            return

        print(f"Play mode switched to: {response['play_mode']}")

        # Handle the response for the default mode
        # if response['play_mode'] == 'default' or 'shuffle':
        #     now_playing = response.get('now_playing', {})
        #     if now_playing:
        #         print(f"Now playing: {now_playing['song_title']} by {now_playing['artist']}")
        #     else:
        #         print("No song is currently playing.")

        print("Current Playlist:")
        playlist = response.get('playlist', [])
        if isinstance(playlist, list) and playlist:
            for song in playlist:
                if isinstance(song, dict):
                    print(f"ID: {song['id']}, Title: {song['song_title']}, Artist: {song['artist']}, "
                          f"Album: {song['album_title']}, Duration: {song['duration']}")
        else:
            print("The playlist is empty.")
    else:
        print("Invalid choice. Please enter 1, 2, or 3.")


def play_next_song_option(client_socket, client_ip, server_ip):
    """
    Handle the user option to play the next song.
    """
    response = play_next_song(client_socket, client_ip, server_ip)


def go_back_option(client_socket, client_ip, server_ip):
    """
    Handle the user option to go back to the previous song.
    """
    response = go_back(client_socket, client_ip, server_ip)
    print(f"Go back response: {response}")


if __name__ == "__main__":
    client()
