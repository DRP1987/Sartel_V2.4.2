# Application Assets

This folder contains visual resources for the CAN Bus Monitoring application.

## Customizing the Application Icon

Replace these files with your custom icons:

- **`icon.png`** - Used on Linux/Mac (recommended: 256x256 or 512x512 pixels)
- **`icon.ico`** - Used on Windows (multi-size icon: 16x16, 32x32, 48x48, 256x256)

### Current Icon

The default icon is a blue circle with "CAN" text, providing a professional appearance out of the box.

## Customizing the Application Name

To change the application name displayed in all windows:

1. Edit `config/app_config.py`
2. Update the `APP_NAME` constant:
   ```python
   APP_NAME = "Your Custom Name"
   ```
3. Restart the application

## Icon Creation Tools

### Online Tools
- **Favicon.io** - https://favicon.io/ (Free, easy-to-use)
- **RealFaviconGenerator** - https://realfavicongenerator.net/

### Desktop Software
- **GIMP** - Free and open-source image editor (https://www.gimp.org/)
- **Inkscape** - Free vector graphics editor (https://inkscape.org/)
- **Paint.NET** - Free image editor for Windows (https://www.getpaint.net/)

### Tips for Icon Design

1. **Keep it simple** - Icons should be recognizable at small sizes (16x16)
2. **Use high contrast** - Ensure icon is visible on both light and dark backgrounds
3. **Test at multiple sizes** - Icon should look good at 16x16, 32x32, and larger
4. **Save with transparency** - Use PNG format with alpha channel for best results

## File Formats

### PNG Format (icon.png)
- Recommended size: 256x256 or 512x512 pixels
- Include alpha channel (transparency)
- Used by default on Linux and macOS

### ICO Format (icon.ico)
- Should contain multiple sizes: 16x16, 32x32, 48x48, 256x256
- Windows native icon format
- Can be created from PNG using tools like GIMP or online converters

## Logo File

The `logo.png` file is used for:
1. **Splash screen** - Displayed during application startup (3 seconds)
2. **Application UI** - May be used within the application interface

### Customizing the Splash Screen Logo

Replace `logo.png` with your company logo:

- **Recommended size**: 400x400 to 800x800 pixels
- **Format**: PNG with transparency (alpha channel)
- **Aspect ratio**: Any (will be scaled to fit splash screen)
- **Current size**: 150x50 pixels (company logo)

### Splash Screen Configuration

To customize splash screen behavior, edit `config/app_config.py`:

```python
# Splash screen settings
LOGO_PATH = "assets/logo.png"           # Path to logo image
SPLASH_DURATION = 3000                  # Display time in milliseconds
SHOW_SPLASH_SCREEN = True               # Enable/disable splash screen
```

**Examples:**

- Change duration to 5 seconds: `SPLASH_DURATION = 5000`
- Disable splash screen: `SHOW_SPLASH_SCREEN = False`
- Use different logo: `LOGO_PATH = "assets/my_custom_logo.png"`

### Splash Screen Features

✅ **Professional appearance** - Displays company branding on startup  
✅ **Configurable duration** - Adjust display time (default: 3 seconds)  
✅ **Graceful fallback** - Works even if logo file is missing  
✅ **Frameless design** - Clean, modern appearance without borders  
✅ **Auto-centered** - Automatically positioned at screen center  
✅ **Optional** - Can be disabled via configuration
