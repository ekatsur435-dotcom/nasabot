import os
import tempfile
import base64
from io import BytesIO
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests

app = Flask(__name__)

# Colors
WHITE = (255, 255, 255)
RED = (220, 53, 69)
GRAY = (170, 170, 170)
GREEN_COLOR = (40, 167, 69)
BLUE_COLOR = (0, 123, 255)

def download_image(url):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image: {e}")
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
            break
    
    if not font_path:
        font_path = None
    
    # Parse font sizes from data or use defaults
    try:
        font_size_top = int(data.get('font_size_top', '30px').replace('px', '')) if data else 30
        font_size_right = int(data.get('font_size_right', '30px').replace('px', '')) if data else 30
        font_size_title = int(data.get('font_size_title', '33px').replace('px', '')) if data else 33
        font_size_price = int(data.get('font_size_price', '26px').replace('px', '')) if data else 26
    except:
        font_size_top = 30
        font_size_right = 30
        font_size_title = 33
        font_size_price = 26
    
    try:
        fonts['large'] = ImageFont.truetype(font_path, font_size_title) if font_path else ImageFont.load_default()
        fonts['medium'] = ImageFont.truetype(font_path, font_size_price) if font_path else ImageFont.load_default()
        fonts['small'] = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
        fonts['badge_top'] = ImageFont.truetype(font_path, font_size_top) if font_path else ImageFont.load_default()
        fonts['badge_right'] = ImageFont.truetype(font_path, font_size_right) if font_path else ImageFont.load_default()
        fonts['badge'] = ImageFont.truetype(font_path, font_size_right) if font_path else ImageFont.load_default()
        fonts['emoji'] = ImageFont.truetype(font_path, 26) if font_path else ImageFont.load_default()
        fonts['brand'] = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()
        fonts['brand_small'] = ImageFont.truetype(font_path, 22) if font_path else ImageFont.load_default()
    except Exception:
        fonts = {k: ImageFont.load_default() for k in ['large', 'medium', 'small', 'badge', 'badge_top', 'badge_right', 'emoji', 'brand', 'brand_small']}
    
    return fonts

def create_gradient_overlay(width, height):
    """Create gradient overlay for better text readability"""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Gradient from bottom
    for y in range(height):
        alpha = int(180 * (y / height))
        draw.line([(0, height - y - 1), (width, height - y - 1)], fill=(0, 0, 0, min(alpha, 180)))
    
    return overlay

def draw_text_with_emoji(draw, text, font, x, y, fill=(255, 255, 255)):
    """Draw text with emoji support"""
    draw.text((x, y), text, font=font, fill=fill)

def download_logo(url):
    """Download logo image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading logo: {e}")
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
    
    # Set dimensions
    if template == 'vertical':
        WIDTH, HEIGHT = 1080, 1350
    else:  # square
        WIDTH, HEIGHT = 1080, 1080
    
    # Download background image
    image_url = data.get('image_url', '')
    if not image_url:
        return None
    
    img = download_image(image_url)
    if not img:
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
    
    # Bottom content - Title and Price (moved up by 20px to avoid logo overlap)
    bottom_y = HEIGHT - 200  # Was 180, now 200 (20px higher)
    
    # Title
    title = data.get('title', '')
    if title:
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
        
        # Draw title lines
        line_y = bottom_y - (len(lines) - 1) * 55
        for line in lines[:2]:  # Max 2 lines
            draw.text((MARGIN, line_y), line, font=fonts['large'], fill=WHITE)
            line_y += 55
    
    # Price
    price = data.get('price', '')
    if price:
        price_y = bottom_y + 70
        draw.text((MARGIN, price_y), price, font=fonts['medium'], fill=WHITE)
    
    # NAS-A HOMES Logo (position based on logo_position parameter)
    logo_url = data.get('logo_url', '')
    logo_position = data.get('logo_position', 'bottom-left')
    
    # Calculate position based on logo_position
    logo_margin = 30
    logo_size = 100  # Размер круглого логотипа
    text_offset = 110  # Отступ для текста от логотипа
    
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
        logo_img = download_logo(logo_url)
        if logo_img:
            # Create circular logo with radial gradient fade
            circular_logo = create_radial_gradient_logo(logo_img, logo_size)
            
            # Paste onto template
            template_img.paste(circular_logo, (logo_x, logo_y), circular_logo)
    
    # Draw NAS-A text next to logo
    draw.text((text_x, text_y), "NAS-A", font=fonts['brand'], fill=WHITE)
    bbox = draw.textbbox((text_x, text_y), "NAS-A", font=fonts['brand'])
    homes_x = bbox[2] + 6
    
    # HOMES - red
    draw.text((homes_x, text_y), "HOMES", font=fonts['brand'], fill=RED)
    
    # Subtitle (increased font size)
    sub_y = text_y + 45
    draw.text((text_x, sub_y), "REAL ESTATE & INVEST", font=fonts['brand_small'], fill=GRAY)
    
    # Convert to RGB for saving
    final_img = template_img.convert('RGB')
    
    return final_img

@app.route('/generate', methods=['POST'])
def generate():
    """Generate Instagram template image"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Required fields
        if not data.get('image_url'):
            return jsonify({'error': 'image_url is required'}), 400
        
        # Generate template
        template_type = data.get('template', 'vertical')
        img = create_instagram_template(data, template_type)
        
        if not img:
            return jsonify({'error': 'Failed to generate image'}), 500
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG', quality=95)
        temp_file.close()
        
        # Read and encode to base64
        with open(temp_file.name, 'rb') as f:
            img_data = f.read()
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        # Return base64 encoded image
        base64_image = base64.b64encode(img_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image_url': f'data:image/jpeg;base64,{base64_image}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
