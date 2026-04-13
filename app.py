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

def get_fonts():
    """Get fonts (fallback to default if not found)"""
    fonts = {}
    
    # Try to find system fonts
    font_paths = [
        "/Library/Fonts/Arial Unicode MS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    
    font_path = None
    for path in font_paths:
        if os.path.exists(path):
            font_path = path
            break
    
    if not font_path:
        font_path = None
    
    try:
        fonts['large'] = ImageFont.truetype(font_path, 48) if font_path else ImageFont.load_default()
        fonts['medium'] = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()
        fonts['small'] = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()
        fonts['badge'] = ImageFont.truetype(font_path, 24) if font_path else ImageFont.load_default()
        fonts['emoji'] = ImageFont.truetype(font_path, 26) if font_path else ImageFont.load_default()
        fonts['brand'] = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()
        fonts['brand_small'] = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
    except Exception:
        fonts = {k: ImageFont.load_default() for k in ['large', 'medium', 'small', 'badge', 'emoji', 'brand', 'brand_small']}
    
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
            new_height = HEIGHT
            new_width = int(new_height * bg_ratio)
            bg_image = bg_image.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - WIDTH) // 2
            bg_image = bg_image.crop((left, 0, left + WIDTH, HEIGHT))
        else:
            new_width = WIDTH
            new_height = int(new_width / bg_ratio)
            bg_image = bg_image.resize((new_width, new_height), Image.LANCZOS)
            top = (new_height - HEIGHT) // 2
            bg_image = bg_image.crop((0, top, WIDTH, top + HEIGHT))
    else:
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
    fonts = get_fonts()
    
    # Starting Y position for badges
    badge_y = MARGIN
    
    # 1. Label badge (green) - left side
    label = data.get('label', '')
    if label:
        badge_text = f" {label} "
        bbox = draw.textbbox((0, 0), badge_text, font=fonts['badge'])
        badge_width = bbox[2] - bbox[0] + 20
        badge_height = bbox[3] - bbox[1] + 16
        
        draw.rounded_rectangle(
            [(MARGIN, badge_y), (MARGIN + badge_width, badge_y + badge_height)],
            radius=8,
            fill=GREEN_COLOR
        )
        draw.text((MARGIN + 10, badge_y + 8), badge_text, font=fonts['badge'], fill=WHITE)
        
        badge_y = badge_y + badge_height + 10
    
    # 2. City badge (green) - under label
    city = data.get('city', '')
    if city:
        city_badge_text = f" {city} "
        bbox = draw.textbbox((0, 0), city_badge_text, font=fonts['badge'])
        city_badge_width = bbox[2] - bbox[0] + 20
        city_badge_height = bbox[3] - bbox[1] + 16
        
        draw.rounded_rectangle(
            [(MARGIN, badge_y), (MARGIN + city_badge_width, badge_y + city_badge_height)],
            radius=8,
            fill=GREEN_COLOR
        )
        draw.text((MARGIN + 10, badge_y + 8), city_badge_text, font=fonts['badge'], fill=WHITE)
    
    # Right side badges
    right_badge_y = MARGIN
    badge_spacing = 10
    
    # 3. Villa badge (blue)
    property_type = data.get('property_type', '')
    if property_type:
        villa_text = f" {property_type} "
        bbox = draw.textbbox((0, 0), villa_text, font=fonts['badge'])
        villa_width = bbox[2] - bbox[0] + 20
        villa_height = bbox[3] - bbox[1] + 16
        
        villa_x = WIDTH - MARGIN - villa_width
        
        draw.rounded_rectangle(
            [(villa_x, right_badge_y), (WIDTH - MARGIN, right_badge_y + villa_height)],
            radius=8,
            fill=BLUE_COLOR
        )
        draw.text((villa_x + 10, right_badge_y + 8), villa_text, font=fonts['badge'], fill=WHITE)
        
        right_badge_y = right_badge_y + villa_height + badge_spacing
    
    # 4. Status badge (blue) - Sale/Rent
    property_status = data.get('property_status', '')
    if property_status:
        status_text = f" {property_status} "
        bbox = draw.textbbox((0, 0), status_text, font=fonts['badge'])
        status_width = bbox[2] - bbox[0] + 20
        status_height = bbox[3] - bbox[1] + 16
        
        status_x = WIDTH - MARGIN - status_width
        
        draw.rounded_rectangle(
            [(status_x, right_badge_y), (WIDTH - MARGIN, right_badge_y + status_height)],
            radius=8,
            fill=BLUE_COLOR
        )
        draw.text((status_x + 10, right_badge_y + 8), status_text, font=fonts['badge'], fill=WHITE)
        
        right_badge_y = right_badge_y + status_height + badge_spacing
    
    # 5. Distance to beach badge (blue)
    distance = data.get('distance_to_beach', '')
    if distance:
        dist_text = f" {distance} "
        bbox = draw.textbbox((0, 0), dist_text, font=fonts['badge'])
        dist_width = bbox[2] - bbox[0] + 20
        dist_height = bbox[3] - bbox[1] + 16
        
        dist_x = WIDTH - MARGIN - dist_width
        
        draw.rounded_rectangle(
            [(dist_x, right_badge_y), (WIDTH - MARGIN, right_badge_y + dist_height)],
            radius=8,
            fill=BLUE_COLOR
        )
        draw.text((dist_x + 10, right_badge_y + 8), dist_text, font=fonts['badge'], fill=WHITE)
    
    # Bottom content - Title
    bottom_y = HEIGHT - 180
    
    # Title
    title = data.get('title', '')
    if title:
        max_width = WIDTH - 2 * MARGIN - 200
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
        
        line_y = bottom_y - (len(lines) - 1) * 55
        for line in lines[:2]:
            draw.text((MARGIN, line_y), line, font=fonts['large'], fill=WHITE)
            line_y += 55
    
    # NAS-A HOMES branding (bottom right)
    brand_x = WIDTH - 250
    brand_y = HEIGHT - 100
    
    # NAS-A - white
    draw.text((brand_x, brand_y), "NAS-A", font=fonts['brand'], fill=WHITE)
    bbox = draw.textbbox((brand_x, brand_y), "NAS-A", font=fonts['brand'])
    homes_x = bbox[2] + 6
    
    # HOMES - red
    draw.text((homes_x, brand_y), "HOMES", font=fonts['brand'], fill=RED)
    
    # Subtitle
    sub_y = brand_y + 45
    draw.text((brand_x, sub_y), "REAL ESTATE & INVEST", font=fonts['brand_small'], fill=GRAY)
    
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
        
        if not data.get('image_url'):
            return jsonify({'error': 'image_url is required'}), 400
        
        # Generate template
        template_type = data.get('template', 'vertical')
        img = create_instagram_template(data, template_type)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.save(temp_file.name, 'JPEG', quality=95)
        temp_file.close()
        
        # Convert to base64
        with open(temp_file.name, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Clean up
        os.unlink(temp_file.name)
        
        return jsonify({
            'success': True,
            'image_url': f'data:image/jpeg;base64,{img_base64}',
            'template': template_type
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for UptimeRobot"""
    return jsonify({'status': 'ok', 'service': 'NASA Instagram API'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
