import os
import json
from pinterest_publisher_playwright import STATE_FILE, process_publishing_tasks

def publish_pins_from_json(json_path: str, image_dir: str, max_uploads: int = 25):
    """
    Reads a JSON file containing single pin data, looks for images in image_dir, 
    and publishes all of them to Pinterest using the same data.
    
    Expected JSON format:
    {
        "title": "My Pin Title",
        "description": "My Pin Description",
        "link": "https://example.com",
        "board_name": "My Board"
    }
    """
    if not os.path.exists(STATE_FILE):
        print(f"Error: {STATE_FILE} not found.")
        print("Please run `python pinterest_login_playwright.py` first to save your login session.")
        return

    if not os.path.exists(json_path):
        print(f"Error: Could not find JSON file at {json_path}")
        return

    published_dir = os.path.join(image_dir, "Published")
    os.makedirs(published_dir, exist_ok=True)

    print(f"Loading data from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        post_data = json.load(f)

    valid_extensions = ('.webp', '.jpg', '.jpeg', '.png')
    
    # Find already published slugs
    published_slugs = set()
    if os.path.exists(published_dir):
        for pub_file in os.listdir(published_dir):
            if os.path.isfile(os.path.join(published_dir, pub_file)):
                pub_slug, _ = os.path.splitext(pub_file)
                published_slugs.add(pub_slug)
    
    # Collect tasks
    tasks_to_run = []
    for file_name in os.listdir(image_dir):
        if len(tasks_to_run) >= max_uploads:
            break
            
        image_path = os.path.join(image_dir, file_name)
        if os.path.isfile(image_path) and file_name.lower().endswith(valid_extensions):
            slug, _ = os.path.splitext(file_name)
            
            if slug in published_slugs:
                print(f"Skipping {file_name} - already published.")
                continue
            
            # Apply the same post_data to every valid image
            tasks_to_run.append((image_path, file_name, slug, post_data))

    process_publishing_tasks(tasks_to_run, published_dir)

if __name__ == "__main__":
    print("="*60)
    print("BULK PINTEREST PUBLISHER (JSON MODE)")
    print("="*60)
    
    # Change these paths if your images or JSON file are located elsewhere
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, "pinterest_data.json")
    images_directory = os.path.join(current_dir, "images")
    
    if not os.path.exists(images_directory):
        print(f"Creating images directory at {images_directory}...")
        os.makedirs(images_directory, exist_ok=True)
        print("Please place your images in this folder and run the script again.")
    else:
        publish_pins_from_json(json_file_path, images_directory)
