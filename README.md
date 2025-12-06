# uLogger Examples

This repository contains example implementations for publishing logs to the uLogger service. uLogger provides a centralized logging platform that accepts log messages via MQTT and processes them for analysis and monitoring.

## Table of Contents

- [Python Log Publishing Example](#python-log-publishing-example)
- [Build Pipeline Integration](#build-pipeline-integration)

## Python Log Publishing Example

The `python-log-publish` directory contains a complete Python implementation for publishing logs to uLogger via MQTT.

### Overview

The Python example demonstrates how to:
- Connect to the uLogger MQTT broker (`mqtt.ulogger.ai:8883`)
- Format log messages as NDJSON (newline-delimited JSON)
- Handle message batching with proper size limits
- Implement sequence numbering for deduplication
- Manage TLS certificate-based authentication

### Files

- `mqtt_example.py` - Main example implementation with configurable customer/application IDs
- `requirements.txt` - Python dependencies
- `certificate.pem.crt` - TLS client certificate (required for authentication)
- `private.pem.key` - TLS private key (required for authentication)

### Message Format

Log messages are published as NDJSON (newline-delimited JSON) with the following structure:

#### Header (First Line)
```json
{"sequence": 12374, "device_type": "DoorSenseV2", "version": "4.24.2", "git": "bc53443", "serial": "a87de76"}
```

#### Log Messages (Subsequent Lines)
```json
{"t": 0, "lv": 2, "m": "boot ok"}
{"t": 15, "lv": 3, "m": "temp=28.3"}
{"t": 1020, "lv": 4, "m": "warn: radio retry"}
{"t": 1150, "lv": 5, "m": "err: i2c"}
```

### Field Descriptions

#### Header Fields
- `sequence`: Monotonically increasing sequence number for deduplication
- `device_type`: Type of device generating logs
- `version`: Software version
- `git`: Git commit hash
- `serial`: Device serial number

#### Log Message Fields
- `t`: Timestamp (Unix timestamp in seconds)
- `lv`: Log level (1=DEBUG, 2=INFO, 3=WARNING, 4=ERROR, 5=CRITICAL)
- `m`: Log message content

### MQTT Configuration

- **Broker**: `mqtt.ulogger.ai`
- **Port**: `8883` (TLS/SSL)
- **Topic Format**: `/logs/v0/{customer_id}/{application_id}`
- **Authentication**: TLS client certificates

### Message Batching and Size Limits

- **Maximum batch size**: 128KB
- **Batching behavior**: Messages exceeding 128KB are automatically split into multiple batches
- **Error handling**: Messages over 128KB are rejected with `CLIENT_ERROR: PAYLOAD_LIMIT_EXCEEDED`

Each batch always begins with a header line containing the sequence number, followed by one or more log message lines.

### Sequence Numbers

Sequence numbers serve as deduplication identifiers:
- Must be monotonically increasing within an application session
- Should start with a random number at application startup
- Does not need to be globally unique across all time
- Should not repeat in the near future to ensure proper deduplication

### Setup and Usage

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Certificate Setup**
   - Place your TLS client certificate in `certificate.pem.crt`
   - Place your TLS private key in `private.pem.key`
   - Ensure both files are in the same directory as the Python script

3. **Configure Customer and Application IDs**
   
   Edit `mqtt_example.py` and update the following variables:
   ```python
   CUSTOMER_ID = 123456789  # Replace with your actual customer ID
   APPLICATION_ID = 123456789  # Replace with your actual application ID
   ```

4. **Run the Example**
   ```bash
   python mqtt_example.py
   ```

### Code Example

```python
from mqtt_example import ULoggerClient, LogLevel

# Initialize client
client = ULoggerClient(customer_id=12345)
client.connect()

# Define header information
header = {
    "git": "bc53443",
    "serial": "a87de76", 
    "version": "4.24.2",
    "device_type": "DoorSenseV2"
}

# Create log batch
logs = [
    {"msg": "boot ok", "level": LogLevel.INFO},
    {"msg": "temp=28.3", "level": LogLevel.INFO},
    {"msg": "warn: radio retry", "level": LogLevel.WARNING},
    {"msg": "err: i2c", "level": LogLevel.ERROR}
]

# Publish logs
client.publish_logs(header, logs, application_id=67890)

# Clean up
client.disconnect()
```

### Error Handling

The client includes error handling for common scenarios:
- Missing certificate files
- Connection failures
- Publishing failures
- Automatic batch splitting for oversized payloads

### Log Levels

The implementation supports standard log levels:
- `LogLevel.DEBUG` (1)
- `LogLevel.INFO` (2)
- `LogLevel.WARNING` (3)
- `LogLevel.ERROR` (4)
- `LogLevel.CRITICAL` (5)

### Security Considerations

- TLS certificates should be kept secure and not committed to version control
- Use appropriate file permissions for certificate and key files
- Consider certificate rotation policies for production deployments

### Troubleshooting

1. **Certificate Issues**: Ensure certificate and key files exist and have correct permissions
2. **Connection Issues**: Verify network connectivity to `mqtt.ulogger.ai:8883`
3. **Publishing Failures**: Check that customer and application IDs are correctly configured
4. **Size Limit Errors**: The client automatically handles batch splitting, but individual log messages should not exceed 128KB

### Dependencies

- `paho-mqtt>=1.6.1` - MQTT client library for Python

## Build Pipeline Integration

The `example_upload` directory demonstrates how to integrate uLogger firmware upload automation into your CI/CD pipeline using GitHub Actions.

### Overview

This example shows how to:
- Automatically build and upload firmware to uLogger during CI/CD
- Extract and track version information from git tags and commits
- Securely manage MQTT certificates and authentication credentials
- Integrate with existing GitHub Actions workflows
- Monitor and verify firmware uploads

### Key Features

- **Automated Builds**: Trigger firmware builds on push, pull requests, or manual dispatch
- **Version Management**: Automatic semantic versioning from git tags with fallback to development versions
- **GitHub Secrets**: Secure credential management for certificates and API keys
- **Artifact Storage**: Automatic backup of built firmware files
- **Flexible Configuration**: Easy integration with any build system (Make, CMake, custom scripts, etc.)

### Quick Example

The workflow automatically:
1. Checks out your repository
2. Builds your firmware (or uses the provided sample)
3. Extracts version from git tags or generates a development version
4. Uploads the firmware to uLogger with metadata (git hash, branch, version)
5. Stores the built firmware as a GitHub artifact

### Setup

1. Fork or clone the [uLogger example_upload repository](https://github.com/ulogger-ai/example_upload)
2. Configure GitHub Secrets with your uLogger credentials:
   - `ULOGGER_CUSTOMER_ID`
   - `ULOGGER_APPLICATION_ID`
   - `ULOGGER_DEVICE_TYPE`
   - `ULOGGER_CERT_DATA` (MQTT certificate)
   - `ULOGGER_KEY_DATA` (MQTT private key)
3. Customize `.github/workflows/build-and-upload.yml` with your build commands
4. Push changes and the workflow will automatically upload to uLogger

### Repository

For complete documentation and working examples, visit: [ulogger-ai/example_upload](https://github.com/ulogger-ai/example_upload)

For more information about uLogger or additional examples, please refer to the official documentation.