import ssl
import time
import random
import json
import paho.mqtt.client as mqtt
import sys
import os

CUSTOMER_ID = 123456789 # Example customer ID
APPLICATION_ID = 123456789 # Example application ID

MAX_SIZE = 128 * 1024

class LogLevel:
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5


class ULoggerClient:
    """A client for publishing logs to the ulogger MQTT broker."""
    
    def __init__(self, customer_id, broker="mqtt.ulogger.ai", port=8883, 
                 cert_file="certificate.pem.crt", key_file="private.pem.key"):
        """Initialize the ULogger client.
        
        Args:
            customer_id: The customer ID for the ulogger service
            broker: The MQTT broker hostname
            port: The MQTT broker port
            cert_file: Path to the certificate file
            key_file: Path to the private key file
        """
        self.customer_id = customer_id
        self.broker = broker
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.client = None
        self.sequence = random.randint(0, 999999)  # Random starting sequence number

        if os.path.exists(self.cert_file) is False or os.path.exists(self.key_file) is False:
            print("Certificate or key file not found. Please provide valid paths.")
            sys.exit(1)
        
    def connect(self):
        """Connect to the ulogger MQTT broker."""
        self.client = mqtt.Client(client_id=f"cust-{self.customer_id}")
        # Set certs for ulogger broker
        self.client.tls_set(
            ca_certs=None,  # Set to CA file if required by broker
            certfile=self.cert_file,
            keyfile=self.key_file,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
        self.client.connect(self.broker, port=self.port)
        self.client.loop_start()
        
    def disconnect(self):
        """Disconnect from the ulogger MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
            
    def publish_logs(self, header, log_batch, application_id):
        """Publish a batch of logs to the ulogger broker.
        
        Args:
            header: Header information for the log batch
            log_batch: List of log entries to publish
            application_id: Application identifier for the logs
        """
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
            
        # Determine topic
        topic = f"logs/v0/{self.customer_id}/{application_id}"

        # Prepare NDJSON log lines (excluding header)
        log_lines = []
        for log in log_batch:
            ndjson_log = {
                "t": time.time(),
                "lv": log.get("level", 0),
                "m": log.get("msg", ""),
            }
            log_lines.append(json.dumps(ndjson_log))

        i = 0
        while i < len(log_lines):
            # Update sequence for each batch
            current_header = header.copy()  # Don't modify the original
            current_header["sequence"] = self.sequence
            
            # Always start a new batch with the header
            batch = [json.dumps(current_header) + "\n"]
            batch_size = len(batch[0].encode("utf-8"))

            # Add as many log lines as will fit
            while i < len(log_lines):
                line = log_lines[i] + "\n"
                line_bytes = line.encode("utf-8")
                if batch_size + len(line_bytes) > MAX_SIZE:
                    break
                batch.append(line)
                batch_size += len(line_bytes)
                i += 1
            payload = "".join(batch)
            print(f"Publishing batch of {len(batch)-1} logs, total size {batch_size} bytes, sequence {self.sequence}")
            print(payload)
            
            result = self.client.publish(topic, payload)
            if result.rc == 0:
                print(f"Published {len(batch)-1} logs to ulogger MQTT topic {topic}")
            else:
                print(f"Failed to publish to ulogger MQTT topic {topic}: {result.rc}")
                sys.exit()
            
            # Increment sequence number for each batch
            self.sequence += 1


def main():
    """Main function to connect to ulogger broker and publish example log messages."""
    print("Starting ulogger example publisher...")

    if CUSTOMER_ID == 123456789 or APPLICATION_ID == 123456789:
        print("Please set CUSTOMER_ID and APPLICATION_ID to your actual values in the script.")
        sys.exit(1)
    
    # Create and connect to ulogger client
    ulogger = ULoggerClient(CUSTOMER_ID)
    ulogger.connect()
    
    # Wait a moment for connection to establish
    time.sleep(2)
        
    # Generate and publish example logs for node application
    print("Publishing node logs...")
    header = {
        "git": "25ed6bd", # user repo git commit hash embedded at build-time
        "serial": "10394650",
        "version": "v2.1.0",
        "device_type": "Gateway"
    }
    
    # Example log batch
    node_logs = [
        {
            "msg": "Node sensor reading: temperature 25.3C",
            "time": time.time(),
            "level": LogLevel.INFO,
            "name": "",
            "device_type": "device_a"
        },
        {
            "msg": "Node battery level: 27%",
            "time": time.time() + 0.005,
            "level": LogLevel.WARNING,
            "name": "node_debug", 
            "device_type": "node"
        }
    ]
    
    ulogger.publish_logs(header, node_logs, APPLICATION_ID)
    
    print("All example messages published successfully!")
    
    # Clean up
    ulogger.disconnect()
    print("Disconnected from ulogger broker")


if __name__ == "__main__":
    main()
