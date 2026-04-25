import os
import tempfile
import base64
import logging
import sys
from io import BytesIO
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHANNEL_ID = os.environ.get("TG_CHANNEL_ID", "")
TG_WEBHOOK_SECRET = os.environ.get("TG_WEBHOOK_SECRET", "")

# Colors
WHITE = (255, 255, 255)
RED = (220, 53, 69)
GRAY = (170, 170, 170)
GREEN_COLOR = (40, 167, 69)
BLUE_COLOR = (0, 123, 255)

def telegram_api(method, payload=None):
    """Call Telegram Bot API."""
    if not TG_BOT_TOKEN:
        logger.error("TG_BOT_TOKEN is not configured")
        return {
            "ok": False,
            "error_code": 500,
            "description": "TG_BOT_TOKEN is not configured",
        }

    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/{method}"
    logger.info(f"Telegram API call: {method} to chat_id: {payload.get('chat_id') if payload else 'N/A'}")

    try:
        response = requests.post(url, json=payload or {}, timeout=30)
        result = response.json()
        if not result.get('ok'):
            logger.error(f"Telegram API error: {result}")
        else:
            logger.info(f"Telegram API success: {method}")
        return result
    except Exception as e:
        logger.error(f"Telegram API exception: {e}")
        return {
            "ok": False,
            "error_code": 500,
            "description": str(e),
        }

def telegram_send_message(chat_id, text, reply_to_message_id=None):
    """Send Telegram text message."""
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    return telegram_api("sendMessage", payload)

def telegram_send_photo(chat_id, photo_url, caption=None, reply_to_message_id=None):
    """Send Telegram photo."""
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption[:1024] if caption else None,  # Telegram limit
        "parse_mode": "HTML",
    }

    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id

    return telegram_api("sendPhoto", payload)

def telegram_send_media_group(chat_id, photo_urls, caption=None):
    """Send Telegram media group (carousel)."""
    media = []
    for i, url in enumerate(photo_urls):
        item = {
            "type": "photo",
            "media": url,
        }
        if i == 0 and caption:
            item["caption"] = caption[:1024]
            item["parse_mode"] = "HTML"
        media.append(item)

    payload = {
        "chat_id": chat_id,
        "media": media,
    }

    return telegram_api("sendMediaGroup", payload)

def handle_telegram_command(command, chat_id, message_id):
    """Handle simple Telegram commands."""
    logger.info(f"Handling command: {command} from chat_id: {chat_id}")
    
    if command == "/start":
        return telegram_send_message(
            chat_id,
            "NASA bot is online.\n\nAvailable commands:\n/start\n/help\n/test",
            message_id,
        )

    if command == "/help":
        return telegram_send_message(
            chat_id,
            "Commands:\n"
            "/start - bot status\n"
            "/help - command list\n"
            "/test - test reply and optional channel delivery",
            message_id,
        )

    if command == "/test":
        lines = ["Bot reply: OK"]

        if TG_CHANNEL_ID:
            channel_result = telegram_send_message(
                TG_CHANNEL_ID,
                "NASA test: bot can post to the configured channel.",
            )

            if channel_result.get("ok"):
                lines.append(f"Channel post to {TG_CHANNEL_ID}: OK")
            else:
                lines.append(
                    "Channel post failed: "
                    + channel_result.get("description", "unknown error")
                )
        else:
            lines.append("TG_CHANNEL_ID is not configured.")

        return telegram_send_message(chat_id, "\n".join(lines), message_id)

    return telegram_send_message(
        chat_id,
        "Unknown command. Use /help",
        message_id,
    )

def download_image(url):
    """Download image from URL"""
    try:
        logger.info(f"Downloading image from: {url[:80]}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        logger.info(f"Image downloaded: {img.size}")
        return img
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None

def get_fonts(data=None):
    """Get fonts with dynamic sizes from data"""
    fonts = {}
    
    # Try to find system fonts
    font_paths = [
        "/Library/Fonts/Arial Unicode MS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/arial.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            logger.info(f"Using font: {path}")
            break
    
    if not font_path:
        logger.warning("No system font found, using default")
        font_path = None
    
    # Parse font sizes from data or use defaults
    try:
        font_size_top = int(str(data.get('font_size_top', '42px')).replace('px', '')) if data else 42
        font_size_right = int(str(data.get('font_size_right', '42px')).replace('px', '')) if data else 42
        font_size_title = int(str(data.get('font_size_title', '47px')).replace('px', '')) if data else 47
        font_size_price = int(str(data.get('font_size_price', '26px')).replace('px', '')) if data else 26
    except Exception as e:
        logger.warning(f"Font parse error: {e}, using defaults")
        font_size_top = 30
        font_size_right = 30
        font_size_title = 33
        font_size_price = 26
    
    logger.info(f"Font sizes: top={font_size_top}, right={font_size_right}, title={font_size_title}, price={font_size_price}")
    
    try:
        fonts['large'] = ImageFont.truetype(font_path, font_size_title) if font_path else ImageFont.load_default()
        fonts['medium'] = ImageFont.truetype(font_path, font_size_price) if font_path else ImageFont.load_default()
        fonts['small'] = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
        fonts['badge_top'] = ImageFont.truetype(font_path, font_size_top) if font_path else ImageFont.load_default()
        fonts['badge_right'] = ImageFont.truetype(font_path, font_size_right) if font_path else ImageFont.load_default()
        fonts['badge'] = ImageFont.truetype(font_path, font_size_right) if font_path else ImageFont.load_default()
        fonts['emoji'] = ImageFont.truetype(font_path, 26) if font_path else ImageFont.load_default()
        fonts['brand'] = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()
        fonts['brand_small'] = ImageFont.truetype(font_path, 32) if font_path else ImageFont.load_default()
    except Exception as e:
        logger.error(f"Font loading error: {e}, using defaults")
        fonts = {k: ImageFont.load_default() for k in ['large', 'medium', 'small', 'badge', 'badge_top', 'badge_right', 'emoji', 'brand', 'brand_small']}
    
    return fonts

def create_gradient_overlay(width, height):
    """Create gradient overlay only at bottom (for logo and title area)"""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Gradient height - only bottom 390px area for logo and title (raised 20px more)
    gradient_height = 390
    
    # Gradient from bottom: dark at very bottom, transparent at top of gradient area
    for y in range(gradient_height):
        alpha = int(200 * (y / gradient_height))  # снизу темно (200), к верху прозрачно
        actual_y = height - gradient_height + y
        draw.line([(0, actual_y), (width, actual_y)], fill=(0, 0, 0, min(alpha, 200)))
    
    # Additional dark area at very bottom for logo
    bottom_area = 120
    for y in range(bottom_area):
        actual_y = height - bottom_area + y
        draw.line([(0, actual_y), (width, actual_y)], fill=(0, 0, 0, 160))
    
    return overlay

def draw_text_with_emoji(draw, text, font, x, y, fill=(255, 255, 255)):
    """Draw text with emoji support"""
    draw.text((x, y), text, font=font, fill=fill)

def download_logo(url):
    """Download logo image from URL"""
    try:
        logger.info(f"Downloading logo from: {url[:80]}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        logger.error(f"Error downloading logo: {e}")
        return None

def create_radial_gradient_logo(logo_img, size):
    """Create circular logo with radial gradient fade to edges"""
    # Convert to RGBA
    logo_img = logo_img.convert('RGBA')
    logo_img = logo_img.resize((size, size), Image.LANCZOS)
    
    # Create circular mask with radial gradient
    mask = Image.new('L', (size, size), 0)
    
    # Draw radial gradient
    center = size // 2
    for y in range(size):
        for x in range(size):
            # Distance from center (normalized 0-1)
            dist = ((x - center) ** 2 + (y - center) ** 2) ** 0.5 / (size // 2)
            if dist <= 1.0:
                # Gradient: full opacity in center, fade to transparent at edges
                # Start fading from 60% of radius
                if dist < 0.6:
                    alpha = 255
                else:
                    # Fade from 255 to 0 between 60% and 100% of radius
                    alpha = int(255 * (1 - (dist - 0.6) / 0.4))
                    alpha = max(0, min(255, alpha))
                mask.putpixel((x, y), alpha)
    
    # Create circular logo with gradient mask
    circular_logo = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    circular_logo.paste(logo_img, (0, 0))
    circular_logo.putalpha(mask)
    
    return circular_logo

def create_instagram_template(data, template='vertical'):
    """Create Instagram template with badges"""
    
    logger.info(f"create_instagram_template called with template={template}")
    logger.info(f"Data keys: {list(data.keys())}")
    
    # Check if we should apply full template or just resize
    # Handle both string and boolean values
    apply_template_raw = data.get('apply_template', True)
    if isinstance(apply_template_raw, str):
        apply_template = apply_template_raw.lower() in ('true', '1', 'yes')
    else:
        apply_template = bool(apply_template_raw)
    
    logger.info(f"apply_template raw={apply_template_raw}, parsed={apply_template}")
    
    # Set dimensions
    if template == 'stories':
        WIDTH, HEIGHT = 1080, 1920  # Instagram Stories 9:16
        logger.info("Using stories dimensions: 1080x1920")
    elif template == 'vertical':
        WIDTH, HEIGHT = 1080, 1350  # 4:5 vertical
        logger.info("Using vertical dimensions: 1080x1350")
    else:  # square
        WIDTH, HEIGHT = 1080, 1080  # 1:1 square
        logger.info("Using square dimensions: 1080x1080")
    
    # Download background image
    image_url = data.get('image_url', '')
    if not image_url:
        logger.error("No image_url provided")
        return None
    
    img = download_image(image_url)
    if not img:
        logger.error("Failed to download image")
        return None
    
    # Convert to RGBA
    img = img.convert('RGBA')
    
    # Resize to fill template while maintaining aspect ratio
    img_ratio = img.width / img.height
    template_ratio = WIDTH / HEIGHT
    
    if img_ratio > template_ratio:
        # Image is wider, crop width
        new_height = HEIGHT
        new_width = int(new_height * img_ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        left = (new_width - WIDTH) // 2
        img = img.crop((left, 0, left + WIDTH, HEIGHT))
    else:
        # Image is taller, crop height
        new_width = WIDTH
        new_height = int(new_width / img_ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)
        top = (new_height - HEIGHT) // 2
        img = img.crop((0, top, WIDTH, top + HEIGHT))
    
    logger.info(f"Image resized to: {img.size}")
    
    # If not applying template (other photos), just resize and return
    if not apply_template:
        logger.info("apply_template=False, returning resized image only")
        # Convert to RGB for saving
        final_img = img.convert('RGB')
        return final_img
    
    logger.info("Applying full template with badges and logo")
    
    # Create template with background
    template_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    
    # Paste background
    template_img.paste(img, (0, 0))
    
    # Add gradient overlay
    overlay = create_gradient_overlay(WIDTH, HEIGHT)
    template_img = Image.alpha_composite(template_img, overlay)
    
    draw = ImageDraw.Draw(template_img)
    fonts = get_fonts(data)
    
    MARGIN = 40
    
    # Starting Y position for badges
    badge_y = MARGIN
    
    # 1. Label badge (green) - left side
    label = data.get('label', '')
    if label:
        logger.info(f"Drawing label badge: {label}")
        badge_text = f" {label} "
        bbox = draw.textbbox((0, 0), badge_text, font=fonts['badge_top'])
        badge_width = bbox[2] - bbox[0] + 20
        badge_height = bbox[3] - bbox[1] + 16
        
        draw.rounded_rectangle(
            [(MARGIN, badge_y), (MARGIN + badge_width, badge_y + badge_height)],
            radius=8,
            fill=GREEN_COLOR
        )
        draw.text((MARGIN + 10, badge_y + 8), badge_text, font=fonts['badge_top'], fill=WHITE)
        
        badge_y = badge_y + badge_height + 10
    
    # 2. City badge (green) - under label
    city = data.get('city', '')
    if city:
        logger.info(f"Drawing city badge: {city}")
        city_badge_text = f" {city} "
        bbox = draw.textbbox((0, 0), city_badge_text, font=fonts['badge_top'])
        city_badge_width = bbox[2] - bbox[0] + 20
        city_badge_height = bbox[3] - bbox[1] + 16
        
        draw.rounded_rectangle(
            [(MARGIN, badge_y), (MARGIN + city_badge_width, badge_y + city_badge_height)],
            radius=8,
            fill=GREEN_COLOR
        )
        draw.text((MARGIN + 10, badge_y + 8), city_badge_text, font=fonts['badge_top'], fill=WHITE)
    
    # Right side badges
    right_badge_y = MARGIN
    badge_spacing = 10
    
    # 3. Villa badge (blue)
    property_type = data.get('property_type', '')
    if property_type:
        logger.info(f"Drawing property_type badge: {property_type}")
        villa_text = f" {property_type} "
        bbox = draw.textbbox((0, 0), villa_text, font=fonts['badge_right'])
        villa_width = bbox[2] - bbox[0] + 20
        villa_height = bbox[3] - bbox[1] + 16
        
        villa_x = WIDTH - MARGIN - villa_width
        
        draw.rounded_rectangle(
            [(villa_x, right_badge_y), (WIDTH - MARGIN, right_badge_y + villa_height)],
            radius=8,
            fill=BLUE_COLOR
        )
        draw.text((villa_x + 10, right_badge_y + 8), villa_text, font=fonts['badge_right'], fill=WHITE)
        
        right_badge_y = right_badge_y + villa_height + badge_spacing
    
    # 4. Status badge (blue) - Sale/Rent
    property_status = data.get('property_status', '')
    if property_status:
        logger.info(f"Drawing property_status badge: {property_status}")
        status_text = f" {property_status} "
        bbox = draw.textbbox((0, 0), status_text, font=fonts['badge_right'])
        status_width = bbox[2] - bbox[0] + 20
        status_height = bbox[3] - bbox[1] + 16
        
        status_x = WIDTH - MARGIN - status_width
        
        draw.rounded_rectangle(
            [(status_x, right_badge_y), (WIDTH - MARGIN, right_badge_y + status_height)],
            radius=8,
            fill=BLUE_COLOR
        )
        draw.text((status_x + 10, right_badge_y + 8), status_text, font=fonts['badge_right'], fill=WHITE)
        
        right_badge_y = right_badge_y + status_height + badge_spacing
    
    # 5. Distance to beach badge (blue)
    distance = data.get('distance_to_beach', '')
    if distance:
        logger.info(f"Drawing distance_to_beach badge: {distance}")
        dist_text = f" {distance} "
        bbox = draw.textbbox((0, 0), dist_text, font=fonts['badge_right'])
        dist_width = bbox[2] - bbox[0] + 20
        dist_height = bbox[3] - bbox[1] + 16
        
        dist_x = WIDTH - MARGIN - dist_width
        
        draw.rounded_rectangle(
            [(dist_x, right_badge_y), (WIDTH - MARGIN, right_badge_y + dist_height)],
            radius=8,
            fill=BLUE_COLOR
        )
        draw.text((dist_x + 10, right_badge_y + 8), dist_text, font=fonts['badge_right'], fill=WHITE)
    
    # Bottom content - Title and Price (moved up by 56px total)
    bottom_y = HEIGHT - 236  # Was 216, now 236 (20px higher)
    
    # Title (UPPERCASE)
    title = data.get('title', '').upper()
    if title:
        logger.info(f"Drawing title: {title}")
        # Wrap text if too long
        max_width = WIDTH - 2 * MARGIN - 200  # Leave space for logo
        words = title.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=fonts['large'])
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                if len(lines) >= 2:
                    break
        
        if current_line and len(lines) < 2:
            lines.append(' '.join(current_line))
        
        # Draw title lines with 1.15 line spacing
        # Get actual font size from the large font
        try:
            font_size_large = fonts['large'].size
        except:
            font_size_large = 39
        line_spacing = int(font_size_large * 1.15)  # 1.15 интервал
        line_y = bottom_y - (len(lines) - 1) * line_spacing
        for line in lines[:2]:  # Max 2 lines
            draw.text((MARGIN, line_y), line, font=fonts['large'], fill=WHITE)
            line_y += line_spacing
    
    # Price
    price = data.get('price', '')
    if price:
        logger.info(f"Drawing price: {price}")
        price_y = bottom_y + 70
        draw.text((MARGIN, price_y), price, font=fonts['medium'], fill=WHITE)
    
    # NAS-A HOMES Logo (position based on logo_position parameter)
    logo_url = data.get('logo_url', '')
    logo_position = data.get('logo_position', 'bottom-left')
    
    # Calculate position based on logo_position
    logo_margin = 30
    logo_size = 140  # Размер круглого логотипа (увеличен больше)
    text_offset = 155  # Отступ для текста от логотипа
    
    if logo_position == 'bottom-left':
        logo_x = logo_margin
        logo_y = HEIGHT - logo_size - logo_margin - 20
        text_x = logo_x + text_offset
        text_y = logo_y + 15
    elif logo_position == 'top-left':
        logo_x = logo_margin
        logo_y = logo_margin
        text_x = logo_x + text_offset
        text_y = logo_y + 15
    elif logo_position == 'top-right':
        text_x = WIDTH - 250
        text_y = logo_margin + 15
        logo_x = text_x - text_offset
        logo_y = logo_margin
    elif logo_position == 'center':
        logo_x = (WIDTH - logo_size) // 2 - 100
        logo_y = (HEIGHT - logo_size) // 2
        text_x = logo_x + text_offset
        text_y = logo_y + 15
    else:  # bottom-right (default)
        text_x = WIDTH - 250
        text_y = HEIGHT - logo_size - logo_margin + 15
        logo_x = text_x - text_offset
        logo_y = HEIGHT - logo_size - logo_margin - 20
    
    # Download and paste logo image with radial gradient
    if logo_url:
        logger.info(f"Downloading and placing logo: {logo_url[:80]}...")
        logo_img = download_logo(logo_url)
        if logo_img:
            # Create circular logo with radial gradient fade
            circular_logo = create_radial_gradient_logo(logo_img, logo_size)
            
            # Paste onto template
            template_img.paste(circular_logo, (logo_x, logo_y), circular_logo)
            logger.info(f"Logo placed at ({logo_x}, {logo_y})")
        else:
            logger.warning("Failed to download logo")
    else:
        logger.warning("No logo_url provided")
    
    # Draw NAS-A text next to logo
    draw.text((text_x, text_y), "NAS-A", font=fonts['brand'], fill=WHITE)
    bbox = draw.textbbox((text_x, text_y), "NAS-A", font=fonts['brand'])
    homes_x = bbox[2] + 6
    
    # HOMES - red
    draw.text((homes_x, text_y), "HOMES", font=fonts['brand'], fill=RED)
    
    # Subtitle (increased font size +10px)
    sub_y = text_y + 45
    draw.text((text_x, sub_y), "REAL ESTATE & INVEST", font=fonts['brand_small'], fill=GRAY)
    
    # Phone number - moved below subtitle to avoid overlap
    phone = "+90 542 174 00 29"
    phone_bbox = draw.textbbox((0, 0), phone, font=fonts['brand_small'])
    phone_width = phone_bbox[2] - phone_bbox[0]
    phone_x = WIDTH - logo_margin - phone_width
    phone_y = sub_y  # Align with subtitle row
    draw.text((phone_x, phone_y), phone, font=fonts['brand_small'], fill=WHITE)
    
    # Convert to RGB for saving
    final_img = template_img.convert('RGB')
    
    logger.info("Template created successfully")
    return final_img

@app.route('/generate', methods=['POST'])
def generate():
    """Generate Instagram template image"""
    try:
        data = request.get_json()
        logger.info(f"/generate called with data keys: {list(data.keys()) if data else 'None'}")
        
        if not data:
            logger.error("No data provided")
            return jsonify({'error': 'No data provided'}), 400
        
        # Required fields
        if not data.get('image_url'):
            logger.error("No image_url provided")
            return jsonify({'error': 'image_url is required'}), 400
        
        # Generate template
        template_type = data.get('template', 'vertical')
        logger.info(f"Generating template: {template_type}")
        
        img = create_instagram_template(data, template_type)
        
        if not img:
            logger.error("Failed to generate image")
            return jsonify({'error': 'Failed to generate image'}), 500
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG', quality=95)
        temp_file.close()
        
        logger.info(f"Image saved to temp file: {temp_file.name}")
        
        # Read and encode to base64
        with open(temp_file.name, 'rb') as f:
            img_data = f.read()
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        logger.info(f"Image encoded to base64, size: {len(img_data)} bytes")
        
        # Return base64 encoded image
        base64_image = base64.b64encode(img_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image_url': f'data:image/jpeg;base64,{base64_image}'
        })
        
    except Exception as e:
        logger.exception("Error in /generate")
        return jsonify({'error': str(e)}), 500

@app.route('/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Telegram webhook endpoint for basic bot commands."""
    if TG_WEBHOOK_SECRET:
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if secret != TG_WEBHOOK_SECRET:
            logger.warning(f"Invalid webhook secret: {secret}")
            return jsonify({"ok": False, "error": "invalid secret"}), 403

    update = request.get_json(silent=True) or {}
    logger.info(f"Webhook received: {update.get('update_id', 'N/A')}")
    
    message = update.get("message") or update.get("edited_message")

    if not message:
        logger.info("No message in update")
        return jsonify({"ok": True})

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    message_id = message.get("message_id")
    text = (message.get("text") or "").strip()
    
    logger.info(f"Message from chat_id={chat_id}: {text[:50]}")

    if not chat_id or not text.startswith("/"):
        return jsonify({"ok": True})

    command = text.split()[0].split("@")[0].lower()
    handle_telegram_command(command, chat_id, message_id)

    return jsonify({"ok": True})

@app.route('/telegram/health', methods=['GET'])
def telegram_health():
    """Health check for Telegram configuration."""
    return jsonify({
        'status': 'ok',
        'telegram_configured': bool(TG_BOT_TOKEN),
        'channel_configured': bool(TG_CHANNEL_ID),
        'webhook_secret_configured': bool(TG_WEBHOOK_SECRET),
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
