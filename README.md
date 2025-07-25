# Professional Motion Detector

A robust, professional-grade motion detection system with email alerts, comprehensive error handling, and configurable settings.

## Features

### ✨ Improvements from Original

- **Professional Architecture**: Object-oriented design with proper separation of concerns
- **Robust Error Handling**: Comprehensive exception handling for all operations
- **Advanced Motion Detection**: Uses OpenCV's MOG2 background subtractor for better accuracy
- **Configurable Settings**: YAML-based configuration with sensible defaults
- **Smart Image Management**: Automatic cleanup to prevent disk space issues
- **Professional Logging**: Detailed logging with configurable levels
- **Thread Safety**: Proper synchronization for multi-threaded operations
- **Email Service**: Robust email service with proper MIME handling
- **Motion Cooldown**: Prevents spam alerts with configurable cooldown periods

### 🔧 Core Features

- Real-time motion detection using computer vision
- Email alerts with image attachments
- Configurable sensitivity and detection parameters
- Automatic image cleanup and management
- Professional logging and error handling
- Easy configuration via YAML files

## Installation

1. **Clone or download the files**

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:

   - Copy `.env.template` to `.env`
   - Fill in your email credentials:

   ```bash
   cp .env.template .env
   # Edit .env with your actual values
   ```

4. **Configure the system** (optional):
   - Edit `config.yaml` to adjust detection parameters
   - The system will create a default config if none exists

## Configuration

### Email Setup (Gmail)

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account Settings → Security → App passwords
   - Generate a new app password for this application
3. Use the app password (not your regular password) in `.env`

### Detection Parameters

Edit `config.yaml` to adjust:

- **Sensitivity**: Lower values = more sensitive detection
- **Min Contour Area**: Minimum size of motion to trigger alert
- **Motion Cooldown**: Time between email alerts (prevents spam)

## Usage

### Basic Usage

```bash
python main.py
```

### Test Email Configuration

```bash
python email_service.py
```

### Controls

- **'q' key**: Quit the application
- **Ctrl+C**: Graceful shutdown

## File Structure

```text
motion-detector/
├── main.py              # Main application
├── email_service.py     # Email functionality
├── config.py           # Configuration management
├── config.yaml         # Configuration file
├── .env.template       # Environment variables template
├── .env               # Your actual environment variables (create this)
├── requirements.txt   # Python dependencies
├── images/           # Motion detection images (auto-created)
└── motion_detector.log # Application logs
```

## Configuration Options

### Camera Settings

- `camera_index`: Camera device index (0 for default)
- `frame_width/height`: Video resolution
- `fps`: Frames per second

### Motion Detection

- `sensitivity`: MOG2 background subtractor sensitivity (20-100)
- `motion_threshold`: Threshold for motion detection
- `min_contour_area`: Minimum area to consider as motion
- `motion_cooldown`: Seconds between email alerts

### File Management

- `images_dir`: Directory for storing motion images
- `max_images`: Maximum images to keep (automatic cleanup)

### Display Options

- `show_video`: Show live video feed
- `show_debug`: Show debug windows (motion mask)

### Email Settings

- `enabled`: Enable/disable email notifications

### Logging

- `level`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Troubleshooting

### Common Issues

#### Camera Access

```bash
Error: Cannot access camera
```

**Solution**:

- Check if camera is being used by another application
- Try different camera index values (0, 1, 2...)
- Ensure camera permissions are granted

#### Email Authentication

```bash
Error: SMTP authentication failed
```

**Solution**:

- Use App Password instead of regular Gmail password
- Enable 2-factor authentication first
- Check SMTP server settings

#### Permission Errors

```bash
Error: Permission denied creating images directory
```

**Solution**:

- Run with appropriate permissions
- Check disk space availability
- Ensure write permissions in application directory

### Performance Optimization

#### For Better Detection

- Adjust `sensitivity` (lower = more sensitive)
- Modify `min_contour_area` based on your environment
- Enable debug mode to see motion mask

#### For Resource Management

- Reduce `max_images` if disk space is limited
- Lower `frame_width` and `frame_height` for better performance
- Adjust `fps` based on your needs

## Advanced Usage

### Running as Service (Linux)

Create a systemd service file:

```ini
[Unit]
Description=Motion Detector Service
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/motion-detector
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Custom Email Templates

Modify the `create_motion_alert_message` method in `email_service.py` to customize email content.

### Integration with Home Automation

The system can be extended to integrate with:

- Home Assistant
- MQTT brokers
- Webhook notifications
- SMS alerts

## Security Considerations

1. **Environment Variables**: Never commit `.env` file to version control
2. **Camera Access**: Ensure physical security of camera feed
3. **Email Credentials**: Use app passwords, not main account passwords
4. **Network Security**: Consider running on isolated network if needed

## Development

### Adding New Features

The modular design makes it easy to extend:

```python
# Example: Add webhook notifications
class WebhookService:
    def send_motion_alert(self, image_path):
        # Implementation here
        pass

# In main.py MotionDetector class:
self.webhook_service = WebhookService()
```

### Testing

```bash
# Test email service
python email_service.py

# Test configuration loading
python -c "from config import Config; print(Config())"
```

## Changelog

### v2.0 (Current)

- Complete rewrite with professional architecture
- Added robust error handling and logging
- Implemented configurable YAML settings
- Added automatic image cleanup
- Enhanced email service with proper MIME handling
- Added motion detection cooldown
- Improved thread safety

### v1.0 (Original)

- Basic motion detection
- Simple email alerts
- Minimal error handling

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review log files for error details
3. Ensure all dependencies are installed correctly
4. Verify configuration settings match your environment
