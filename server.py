import socket
import json
import threading
import random
from response import Message
from collections import deque

active_playlist = []
design_playlist = []
play_playlist = deque()
played_history = []
submode = None


def load_catalog():
    """
    Author: Ankita Dewangswami
    This is a function to load the catalog.json file
    It returns the list of songs directly

    :return: It returns the catalog data.
    """
    with open('catalog.json', 'r') as f:
        data = json.load(f)
        return data['catalog']


catalog = load_catalog()


def switch_to_play_mode(mode):
    """ This function is responsible for switching the current playlist into one of the play modes.
    There are three types of play modes to be defined: 1.default 2.shuffle 3. Loop.
    In the default play mode, the play_next_song(submode) is called which plays the first song in the playlist and
    return its details in play_next_response.
    Similarly, in shuffle mode it filters out the design_playlist and call play_next_song(submode) method.

    """
    """Switch the current playlist to play mode and apply the specified submode."""
    global play_playlist, design_playlist, submode
    submode = mode

    if submode == "default":
        design_playlist = deque(song for song in design_playlist if song not in played_history)
        print("Default mode activated. Now playing the first song.")
        play_next_response = play_next_song(submode)

    elif submode == "shuffle":
        available_songs = [song for song in design_playlist if song not in played_history]

        if available_songs:
            design_playlist = deque(random.sample(available_songs, len(available_songs)))
        else:
            design_playlist = deque()
        print(design_playlist, "design_playlist")
        play_next_response = play_next_song(submode)

    elif submode == "loop":
        design_playlist = deque(design_playlist.copy())
        play_next_response = play_next_song(submode)

    if not design_playlist:
        return {"error": "Playlist is empty."}

    playlist_with_details = [{"id": song["id"], "song_title": song["song_title"],
                              "artist": song["artist"], "album_title": song["album_title"],
                              "duration": song["duration"]} for song in design_playlist]

    print("Server is sending playlist:", playlist_with_details)

    return {
        "play_mode": submode,
        "playlist": playlist_with_details,
        "now_playing": play_next_response["now_playing"],
        "message": play_next_response["message"]
    }


def play_next_song(submode):
    """Play the next song based on the current submode."""
    global play_playlist, played_history, design_playlist

    if not design_playlist:
        return {"error": "Playlist is empty."}

    current_song = design_playlist[0]

    song_payload = {
        "id": current_song["id"],
        "song_title": current_song["song_title"],
        "artist": current_song["artist"],
        "album_title": current_song["album_title"],
        "duration": current_song["duration"]
    }

    print("Design playlist inside play_next_song", design_playlist)

    if submode == 'loop':
        current_song = design_playlist.popleft()
        design_playlist.append(current_song)
    else:
        current_song = design_playlist.popleft()
        played_history.append(current_song)

    now_playing_message = f"Now playing: {song_payload['song_title']} by {song_payload['artist']}"

    return {
        "now_playing": song_payload,
        "message": now_playing_message
    }


def go_back():
    """
    Restore the last dequeued song from the played history and
    move it to the front of the play playlist.

    Returns:
        dict: A message indicating the success or failure of the operation.
    """
    global played_history, play_playlist

    if not played_history:
        return {"error": "No previous song to restore."}

    last_played_song = played_history.pop()
    play_playlist.appendleft(last_played_song)

    return {"success": "Restored the previous song.", "restored_song": last_played_song}


def handle_client(client_socket, client_address, server_address):
    """
    This function is used to handle communication with a connected client.
    Args:
        client_socket: This is a socket object created using socket library.
                       This argument represents the connection between the client and server.
        client_address: This argument is a tuple containing the IP address and port number of the client.
                        This argument holds the information about the client's location on the network.
        server_address: This argument is a tuple containing the server's IP address and port number.
    """
    global play_playlist, design_playlist, submode
    while True:
        try:
            header = client_socket.recv(8)
            if not header:
                print("Client disconnected.")
                break
            """
             Receive the payload based on the specified length
             message_length parameter is for the receiving the expected size fo the incoming message payload
             The received payload is then concatenated with the 'header' which contains metadata about the message.
            """
            message_type = header[0]
            message_length = int.from_bytes(header[1:3], 'big')
            payload = client_socket.recv(message_length)
            full_message = header + payload

            """
            The following line of code is to create the Message object from received bytes
            and Validate the checksum (done in the Message.from_bytes method)
            """
            msg = Message.from_bytes(full_message)
            print(f"Message received from {msg.client_ip} to {msg.server_ip} at {msg.timestamp}")
            """
            The below conditional statement is for the flow handling a catalog request, like logging the request,
            preparing a response and sending it back to the client. 
            """
            if msg.message_type == 1:
                print(f"Catalog requested from {client_address}.")
                catalog_data = json.dumps(catalog)
                response = Message(
                    2,
                    catalog_data,
                    client_ip=server_address[0],
                    server_ip=client_address[0]
                )
                client_socket.sendall(response.to_bytes())

            elif msg.message_type == 3:
                """
                The below conditional statement explains the logic for handling a request for the current playlist,
                prepare to send the current playlist to the client by checking if the active playlist is not empty. 
                Finally it sends the updated playlist to the client in the json format.
                """
                print("Current Playlist requested")
                """Send the current playlist to the client."""
                if active_playlist:
                    response_payload = json.dumps({
                        "updated_playlist": active_playlist
                    })

                else:
                    response_payload = json.dumps({
                        "updated_playlist": active_playlist,
                        "error": "No playlist found or playlist is empty."})
                response_msg = Message(6, response_payload, client_ip=server_address[0],
                                       server_ip=client_address[0])
                client_socket.sendall(response_msg.to_bytes())


            elif msg.message_type == 5:
                """
                This conditional statement explains the logic for handling a request to add a song
                to the playlist, such as validating the song ID, checking for duplicates, and 
                send the response back to the client.
                """
                song_id = msg.payload
                print(f"Attempting to add song with ID: {song_id} to the playlist.")

                song = next((item for item in catalog if item['id'] == song_id), None)
                if song:
                    if song not in active_playlist:
                        active_playlist.append(song)
                        design_playlist.append(song)
                        response_payload = json.dumps({
                            "success": f"Song {song_id} added to the playlist.",
                            "updated_playlist": active_playlist
                        })

                    else:

                        response_payload = json.dumps({
                            "updated_playlist": active_playlist,
                            "error": "Song is already in the playlist."
                        })

                else:
                    response_payload = json.dumps({"error": "Invalid song ID."})

                response = Message(6, response_payload, client_ip=client_address[0], server_ip=server_address[0])
                client_socket.sendall(response.to_bytes())


            elif msg.message_type == 7:
                """
                The message_type as 7 is utilized for opening a new playlist in design mode.
                The active playlist is cleared from the server side to get a new playlist.
                """
                print("Opening new playlist on the server.")
                active_playlist.clear()
                design_playlist.clear()
                print("active_playlist", active_playlist)
                response = Message(8, "New playlist opened.", client_ip=client_address[0],
                                   server_ip=server_address[0])
                client_socket.sendall(response.to_bytes())

            elif msg.message_type == 9:
                """This conditional argument statement is used to remove the song from the playlist, it asks for 
                specific id from the client side and removes the song from the active_playlist from the server side. 
                After validating the song ID exists in the active_playlist, the updated current playlist is sent to 
                the client."""
                song_id = msg.payload
                print(f"Attempting to remove song with ID: {song_id} from the playlist.")

                song = next((item for item in active_playlist if item['id'] == song_id), None)

                if song:
                    active_playlist.remove(song)
                    response_payload = json.dumps({
                        "success": f"Song {song_id} removed from the playlist.",
                        "updated_playlist": active_playlist
                    })

                else:
                    response_payload = json.dumps({
                        "error": f"Song ID {song_id} not found in the playlist."
                    })
                response = Message(6, response_payload, client_ip=client_address[0], server_ip=server_address[0])
                client_socket.sendall(response.to_bytes())


            elif msg.message_type == 10:
                """The message_type explains the logic for handling a request to find a song by its ID in the active 
                playlist. It verifies that the current playlist is not empty, and the song with the ID sent by the 
                client exists in the active_playlist. It prepares appropriate response for both successful and 
                unsuccessful searches, and sends the response back to client"""
                print(f"Finding song with ID {msg.payload} in the playlist.")
                song_id = msg.payload
                if not active_playlist:
                    response_payload = json.dumps({"error": "No playlist found or playlist is empty."})
                    response_msg = Message(12, response_payload, client_ip=msg.client_ip, server_ip=msg.server_ip)
                else:
                    found_song = next((song for song in active_playlist if song['id'] == song_id), None)
                    if found_song:
                        response_payload = json.dumps(found_song)
                        response_msg = Message(11, response_payload, client_ip=msg.client_ip, server_ip=msg.server_ip)
                    else:
                        response_payload = json.dumps({"error": f"Song with ID {song_id} not found."})
                        response_msg = Message(12, response_payload, client_ip=msg.client_ip, server_ip=msg.server_ip)

                client_socket.sendall(response_msg.to_bytes())


            elif msg.message_type == 13:
                payload_data = json.loads(msg.payload)
                submode = payload_data.get("mode", None)

                if submode:
                    play_mode_response = switch_to_play_mode(submode)
                    response_data = {
                        "play_mode": play_mode_response["play_mode"],
                        "playlist": play_mode_response["playlist"],
                        "now_playing": play_mode_response["now_playing"]
                    }

                    response_payload = json.dumps(response_data)
                    response = Message(11, response_payload, client_ip=client_address[0], server_ip=server_address[0])
                    client_socket.sendall(response.to_bytes())
                else:
                    print("Error: Invalid submode received.")


            elif msg.message_type == 14:
                print("asked for 14")
                response = switch_to_play_mode('default')
                response_payload = json.dumps(response)
                print("response_payload", response_payload)
                response_msg = Message(11, response_payload, client_ip=client_address[0], server_ip=server_address[0])
                client_socket.sendall(response_msg.to_bytes())

            elif msg.message_type == 15:
                response = go_back()
                response_payload = json.dumps(response)
                response_msg = Message(11, response_payload, client_ip=client_address[0], server_ip=server_address[0])
                client_socket.sendall(response_msg.to_bytes())


        except ConnectionResetError:
            """
            This catch-all exception handler explains the various exceptions that may arise during client communication. 
            It handles the server connection reset, value errors and unexpected exceptions.
            """
            print("Connection reset by peer. The client has disconnected.")
            break
        # except ValueError as e:
        #     print(f"Error processing message: {e}")
        #     error_response = Message(
        #         0,
        #         "Error processing your message.",
        #         client_ip=client_address[0],
        #         server_ip=socket.gethostbyname(socket.gethostname())
        #     )
        #     client_socket.sendall(error_response.to_bytes())
        except Exception as e:
            print(f"Unexpected error: {e}")
            break


def start_server(host='localhost', port=12000):
    """In this client-server architecture, the TCP transport layer protocol is being used.
    This code starts tje server to handle incoming client connections.
    Args:
        host (str): The hostname or IP address to bind the server to. Default is 'localhost'
        port (int): The port number to listen on for incoming connections. Default is 12000
    The below code logic creates a TCP socket using the IPv4 and TCP protocol.
    In addition, the method ensures that the server socket is closed while exiting the loop"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server listening on {host}:{port}")
        try:
            while True:
                client_socket, addr = server_socket.accept()
                print(f"Connection from {addr}")
                handle_client(client_socket, addr, (host, port))
        except KeyboardInterrupt:
            print("\nServer shutting down.")
        finally:
            server_socket.close()


if __name__ == "__main__":
    start_server()
