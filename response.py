import zlib
import json
from datetime import datetime

class Message:
    def __init__(self, message_type, payload, options=0, client_ip='', server_ip=''):
        """
        Author: Ankita Dewangswami
        Message class provides the structured way to encode and decode the message
        :param message_type: type of the message (request or response)
        :param payload: The actual data being sent
        :param options: additonal flags if needed
        :param client_ip: client_ip address
        :param server_ip: server_ip address
        """
        self.message_type = message_type
        self.options = options
        self.payload = payload
        self.client_ip = client_ip
        self.server_ip = server_ip
        self.timestamp = self.get_gmt_timestamp()
        self.checksum = self.calculate_checksum()

    def get_gmt_timestamp(self):
        """With the GMT timestamp message creation, get the current GMT timestamp."""
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S GMT')

    def calculate_checksum(self):
        """Calculate CRC32 checksum for the payload."""
        payload_data = json.dumps({
            "payload": self.payload,
            "client_ip": self.client_ip,
            "server_ip": self.server_ip,
            "timestamp": self.timestamp
        }).encode('utf-8')
        return zlib.crc32(payload_data) & 0xFFFFFFFF

    def to_bytes(self):
        """Convert the message to bytes, including metadata."""
        payload_data = json.dumps({
            "payload": self.payload,
            "client_ip": self.client_ip,
            "server_ip": self.server_ip,
            "timestamp": self.timestamp
        }).encode('utf-8')

        header = bytearray()
        header.append(self.message_type)
        header.extend(len(payload_data).to_bytes(2, 'big'))
        header.append(self.options)
        header.extend(self.checksum.to_bytes(4, 'big'))

        header.extend(payload_data)

        return header

    @classmethod
    def from_bytes(cls, data):
        """Create a Message object from bytes and extract metadata."""
        message_type = data[0]
        length = int.from_bytes(data[1:3], 'big')
        options = data[3]
        checksum = int.from_bytes(data[4:8], 'big')
        payload_data = data[8:8 + length].decode('utf-8')


        full_payload = json.loads(payload_data)
        payload = full_payload.get("payload", "")
        client_ip = full_payload.get("client_ip", "")
        server_ip = full_payload.get("server_ip", "")
        timestamp = full_payload.get("timestamp", "")

        msg = cls(message_type, payload, options, client_ip, server_ip)
        msg.timestamp = timestamp


        if msg.calculate_checksum() != checksum:
            raise ValueError("Checksum mismatch!")

        return msg

