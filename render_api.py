"""
NASA Instagram Template Render API
Deploy to Render.com for free hosting
"""
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import base64
import os
import tempfile

app = Flask(__name__)

# Constants
MARGIN = 50
BLUE_COLOR = (0, 0, 255)
GREEN_COLOR = (76, 175, 80)
WHITE = (255, 255, 255)
RED = (220, 38, 38)
GRAY = (148, 163, 184)

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
    
    # Parse font sizes from data or use defaults (+5px from original)
    try:
        font_size_top = int(data.get('font_size_top', '19px').replace('px', '')) if data else 19
        font_size_right = int(data.get('font_size_right', '19px').replace('px', '')) if data else 19
        font_size_title = int(data.get('font_size_title', '33px').replace('px', '')) if data else 33
        font_size_price = int(data.get('font_size_price', '26px').replace('px', '')) if data else 26
    except:
        font_size_top = 19
        font_size_right = 19
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
        fonts['brand_small'] = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
    except Exception:
        fonts = {k: ImageFont.load_default() for k in ['large', 'medium', 'small', 'badge', 'badge_top', 'badge_right', 'emoji', 'brand', 'brand_small']}
    
    return fonts

def create_gradient_overlay(width, height):
    """Create gradient overlay for better text readability"""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Gradient from bottom
    for y in range(height):
        alpha = int(180 * (1 - y / height) ** 0.5)
        draw.line([(0, height - y - 1), (width, height - y - 1)], fill=(0, 0, 0, min(alpha, 180)))
    
    return overlay

def draw_text_with_emoji(draw, text, font, x, y, fill=(255, 255, 255)):
    """Draw text with emoji support"""
    # Simple implementation - in production use pilmoji
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

def create_instagram_template(data, template='vertical'):
    """Create Instagram template with badges"""
    
    # Set dimensions
    if template == 'vertical':
        WIDTH, HEIGHT = 1080, 1350
    else:  # square
        WIDTH, HEIGHT = 1080, 1080
    
    # Download background image
    bg_image = None
    if data.get('image_url'):
        bg_image = download_image(data['image_url'])
    
    if bg_image:
        # Resize and crop to fit
        bg_ratio = bg_image.width / bg_image.height
        target_ratio = WIDTH / HEIGHT
        
        if bg_ratio > target_ratio:
            # Image is wider, crop width
            new_height = HEIGHT
            new_width = int(new_height * bg_ratio)
            bg_image = bg_image.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - WIDTH) // 2
            bg_image = bg_image.crop((left, 0, left + WIDTH, HEIGHT))
        else:
            # Image is taller, crop height
            new_width = WIDTH
            new_height = int(new_width / bg_ratio)
            bg_image = bg_image.resize((new_width, new_height), Image.LANCZOS)
            top = (new_height - HEIGHT) // 2
            bg_image = bg_image.crop((0, top, WIDTH, top + HEIGHT))
    else:
        # Create blank image
        bg_image = Image.new('RGB', (WIDTH, HEIGHT), (30, 30, 30))
    
    # Convert to RGBA
    img = bg_image.convert('RGBA')
    
    # Create template image
    template_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    
    # Paste background
    template_img.paste(img, (0, 0))
    
    # Add gradient overlay
    overlay = create_gradient_overlay(WIDTH, HEIGHT)
    template_img = Image.alpha_composite(template_img, overlay)
    
    draw = ImageDraw.Draw(template_img)
    fonts = get_fonts(data)
    
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
    
    # Bottom content - Title and Price
    bottom_y = HEIGHT - 180
    
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
            if bbox[2] - bbox[0] > max_width:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                current_line.append(word)
        
        if current_line:
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
    logo_position = data.get('logo_position', 'bottom-right')
    
    if logo_url:
        # Download and use logo image
        logo_img = download_logo(logo_url)
        if logo_img:
            # Resize logo to max 120px width/height
            logo_size = 120
            logo_img.thumbnail((logo_size, logo_size), Image.LANCZOS)
            
            # Calculate position based on logo_position
            logo_margin = 30
            if logo_position == 'bottom-left':
                logo_x = logo_margin
                logo_y = HEIGHT - logo_img.height - logo_margin
            elif logo_position == 'top-left':
                logo_x = logo_margin
                logo_y = logo_margin
            elif logo_position == 'top-right':
                logo_x = WIDTH - logo_img.width - logo_margin
                logo_y = logo_margin
            elif logo_position == 'center':
                logo_x = (WIDTH - logo_img.width) // 2
                logo_y = (HEIGHT - logo_img.height) // 2
            else:  # bottom-right (default)
                logo_x = WIDTH - logo_img.width - logo_margin
                logo_y = HEIGHT - logo_img.height - logo_margin
            
            # Paste logo onto template
            if logo_img.mode == 'RGBA':
                template_img.paste(logo_img, (logo_x, logo_y), logo_img)
            else:
                template_img.paste(logo_img, (logo_x, logo_y))
        else:
            # Fallback to text if logo download fails
            _draw_text_logo(draw, fonts, WIDTH, HEIGHT, logo_position)
    else:
        # Fallback to text logo
        _draw_text_logo(draw, fonts, WIDTH, HEIGHT, logo_position)
    
    # Convert to RGB for saving
    final_img = template_img.convert('RGB')

def _draw_text_logo(draw, fonts, WIDTH, HEIGHT, logo_position):
    """Draw text-based logo as fallback"""
    logo_margin = 30
    brand_x = logo_margin if 'left' in logo_position else WIDTH - 250
    brand_y = HEIGHT - 100 if 'bottom' in logo_position else logo_margin
    
    if logo_position == 'center':
        brand_x = WIDTH // 2 - 100
        brand_y = HEIGHT // 2
    
    # NAS-A - white
    draw.text((brand_x, brand_y), "NAS-A", font=fonts['brand'], fill=WHITE)
    bbox = draw.textbbox((brand_x, brand_y), "NAS-A", font=fonts['brand'])
    homes_x = bbox[2] + 6
    
    # HOMES - red
    draw.text((homes_x, brand_y), "HOMES", font=fonts['brand'], fill=RED)
    
    # Subtitle
    sub_y = brand_y + 45
    draw.text((brand_x, sub_y), "REAL ESTATE & INVEST", font=fonts['brand_small'], fill=GRAY)
    
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
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG', quality=95)
        temp_file.close()
        
        # Convert to base64 (for direct embedding)
        with open(temp_file.name, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Clean up temp file
        os.unlink(temp_file.name)
        
        # In production, you would upload to S3/Cloudinary and return URL
        # For now, return base64 data URL
        return jsonify({
            'success': True,
            'image_url': f'data:image/jpeg;base64,{img_base64}',
            'template': template_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Use PORT from environment (for Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
