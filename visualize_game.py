import re
import os
from PIL import Image, ImageDraw, ImageFont
import imageio

MOVES = ['shield', 'load', 'fireball', 'tsunami', 'mirror']

def load_font(size=20):
    try:
        return ImageFont.truetype("/Library/Fonts/Arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except OSError:
            return ImageFont.load_default()

def load_move_images(static_folder):
    move_images = {}
    for move in MOVES:
        image_path = os.path.join(static_folder, f"{move}.png")
        if os.path.exists(image_path):
            move_images[move] = Image.open(image_path).convert("RGBA")
        else:
            print(f"Warning: Image for {move} not found at {image_path}")
    return move_images

def create_frame(agent1, agent2, move1, move2, loads1, loads2, mirror1, mirror2, move_images):
    # Create a larger blank image
    img = Image.new('RGB', (1000, 600), color='white')
    draw = ImageDraw.Draw(img)
    font = load_font(24)  # Increased font size
    
    # Draw agent1 info
    draw.text((50, 50), f"Agent: {agent1}", fill="black", font=font)
    draw.text((50, 90), f"Loads: {loads1}", fill="black", font=font)
    draw.text((50, 130), f"Move: {move1}", fill="black", font=font)
    draw.text((50, 170), f"Mirror: {'Yes' if mirror1 else 'No'}", fill="black", font=font)
    
    # Draw agent2 info
    draw.text((700, 50), f"Agent: {agent2}", fill="black", font=font)
    draw.text((700, 90), f"Loads: {loads2}", fill="black", font=font)
    draw.text((700, 130), f"Move: {move2}", fill="black", font=font)
    draw.text((700, 170), f"Mirror: {'Yes' if mirror2 else 'No'}", fill="black", font=font)
    
    # Draw move images
    def paste_move_image(move, x, y, flip=False):
        if move in move_images:
            move_img = move_images[move].copy()
            move_img.thumbnail((300, 300))  # Increased size
            if flip:
                move_img = move_img.transpose(Image.FLIP_LEFT_RIGHT)
            img.paste(move_img, (x, y), move_img)
        else:
            draw.rectangle([x, y, x+300, y+300], outline="black", width=2)
            draw.text((x+100, y+140), move, fill="black", font=font)
    
    paste_move_image(move1, 50, 250)
    paste_move_image(move2, 650, 250, flip=True)
    
    return img

def parse_game_file(filename):
    with open(filename, 'r') as file:
        content = file.read()
    
    agents = re.findall(r'(\w+) vs (\w+)', content)
    if not agents:
        raise ValueError(f"Could not find agent names in {filename}")
    agents = agents[0]
    
    moves = re.findall(r'Agent vs Agent: (\w+) vs (\w+)', content)
    if not moves:
        raise ValueError(f"Could not find moves in {filename}")
    
    return agents, moves

def create_gif(agents, moves, move_images, output_filename):
    frames = []
    loads1, loads2 = 0, 0
    mirror1, mirror2 = False, False
    
    for move1, move2 in moves:
        if move1 == 'load':
            loads1 += 1
        if move2 == 'load':
            loads2 += 1
        mirror1 = move1 == 'mirror'
        mirror2 = move2 == 'mirror'
        
        frame = create_frame(agents[0], agents[1], move1, move2, loads1, loads2, mirror1, mirror2, move_images)
        frames.append(frame)
    
    # Save as GIF
    frames[0].save(output_filename, save_all=True, append_images=frames[1:], duration=1000, loop=0)

def main():
    game_file = 'match_results/dj_agent_vs_sample_agent/match_3.txt'
    static_folder = 'static'
    output_filename = 'dj_agent_vs_sample_agent_match3_game_visualization.gif'

    try:
        agents, moves = parse_game_file(game_file)
        move_images = load_move_images(static_folder)
        create_gif(agents, moves, move_images, output_filename)
        print(f"GIF created successfully: {output_filename}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()