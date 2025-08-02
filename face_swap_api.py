#!/usr/bin/env python3
"""
ComfyUI Face Swap API Client
A simple Python program to perform face swapping using ComfyUI API
Based on the tutorial: https://medium.com/@next.trail.tech/how-to-use-comfyui-api-with-python-a-complete-guide-f786da157d37
"""

import json
import requests
import websocket
import uuid
import io
import base64
import argparse
import os
import sys
from PIL import Image

# ComfyUI server configuration
SERVER_ADDRESS = "comfyui.zrok.lcas.group"

# Workflow template based on the provided face swap workflow
WORKFLOW_TEMPLATE = {
  "2": {
    "inputs": {
      "enabled": True,
      "swap_model": "inswapper_128.onnx",
      "facedetection": "YOLOv5l",
      "face_restore_model": "GFPGANv1.3.pth",
      "face_restore_visibility": 1,
      "codeformer_weight": 0.5,
      "detect_gender_input": "no",
      "detect_gender_source": "no",
      "input_faces_index": "0",
      "source_faces_index": "0",
      "console_log_level": 1,
      "input_image": [
        "9",
        0
      ],
      "source_image": [
        "10",
        0
      ]
    },
    "class_type": "ReActorFaceSwap",
    "_meta": {
      "title": "ReActor 🌌 Fast Face Swap"
    }
  },
  "3": {
    "inputs": {
      "image": "PXL_20250726_130415847.MP_Original.jpeg"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "4": {
    "inputs": {
      "image": "PXL_20250614_111909456.MP_Original.jpeg"
    },
    "class_type": "LoadImage",
    "_meta": {
      "title": "Load Image"
    }
  },
  "5": {
    "inputs": {
      "images": [
        "2",
        0
      ]
    },
    "class_type": "PreviewImage",
    "_meta": {
      "title": "Preview image"
    }
  },
  "9": {
    "inputs": {
      "upscale_method": "nearest-exact",
      "scale_by": 0.25000000000000006,
      "image": [
        "3",
        0
      ]
    },
    "class_type": "ImageScaleBy",
    "_meta": {
      "title": "Upscale Image By"
    }
  },
  "10": {
    "inputs": {
      "upscale_method": "nearest-exact",
      "scale_by": 0.25000000000000006,
      "image": [
        "4",
        0
      ]
    },
    "class_type": "ImageScaleBy",
    "_meta": {
      "title": "Upscale Image By"
    }
  },
  "13": {
    "inputs": {
      "images": [
        "2",
        0
      ]
    },
    "class_type": "SaveImageWebsocket",
    "_meta": {
      "title": "SaveImageWebsocket"
    }
  }
}

def upload_image(image_path, server_address, token=None):
    """Upload an image to ComfyUI via API and return the filename"""
    try:
        with open(image_path, 'rb') as f:
            files = {
                'image': (os.path.basename(image_path), f, 'image/jpeg'),
                'overwrite': (None, 'true')
            }
            
            # Prepare headers with Bearer token if provided
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
                print(f"Using Bearer token authentication")
            
            # Upload to ComfyUI's upload endpoint
            response = requests.post(f"https://{server_address}/upload/image", files=files, headers=headers)
            
            if response.status_code == 200:
                print(f"Upload response: {str(response.text)}")
                result = response.json()
                uploaded_filename = result.get('name', os.path.basename(image_path))
                print(f"Successfully uploaded {image_path} as {uploaded_filename}")
                return uploaded_filename
            elif response.status_code == 401:
                print(f"Authentication failed for {image_path}. Please check your token.")
                return None
            else:
                print(f"Failed to upload {image_path}: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"Error uploading image {image_path}: {e}")
        raise e

def queue_prompt(prompt, client_id, server_address, token=None):
    """Queue a prompt for execution"""
    data = {"prompt": prompt, "client_id": client_id}
    try:
        # Prepare headers with Bearer token if provided
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        response = requests.post(f"http://{server_address}/prompt", json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("Authentication failed for prompt queue. Please check your token.")
            return None
        else:
            print(f"Error queuing prompt: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error queuing prompt: {e}")
        return None

def get_history(prompt_id, server_address, token=None):
    """Get execution history for a prompt"""
    try:
        # Prepare headers with Bearer token if provided
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        response = requests.get(f"http://{server_address}/history/{prompt_id}", headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("Authentication failed for history request. Please check your token.")
            return None
        else:
            print(f"Error getting history: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting history: {e}")
        return None

def get_image(filename, subfolder, folder_type, server_address, token=None):
    """Get image data from ComfyUI"""
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    try:
        # Prepare headers with Bearer token if provided
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        response = requests.get(f"http://{server_address}/view", params=params, headers=headers)
        if response.status_code == 200:
            return response.content
        elif response.status_code == 401:
            print("Authentication failed for image request. Please check your token.")
            return None
        else:
            print(f"Error getting image: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting image: {e}")
        return None

def copy_image_to_comfyui_input(image_path, comfyui_input_dir):
    """This function is no longer needed - replaced by upload_image"""
    # This function is deprecated - use upload_image instead
    pass

def face_swap_websocket(input_image_path, source_image_path, output_path, server_address=SERVER_ADDRESS, token=None):
    """Perform face swap using WebSocket method"""
    
    # Generate unique client ID
    client_id = str(uuid.uuid4())
    
    # Upload images to ComfyUI via API
    print("Uploading input image...")
    input_filename = upload_image(input_image_path, server_address, token)
    print("Uploading source image...")
    source_filename = upload_image(source_image_path, server_address, token)
    
    if not input_filename or not source_filename:
        print("Failed to upload images to ComfyUI")
        return False
    
    if not input_filename or not source_filename:
        print("Failed to upload images to ComfyUI")
        return False
    
    # Prepare workflow
    workflow = WORKFLOW_TEMPLATE.copy()
    workflow["3"]["inputs"]["image"] = input_filename
    workflow["4"]["inputs"]["image"] = source_filename
    
    # Set up WebSocket connection
    ws = websocket.WebSocket()
    try:
        # Prepare headers with Bearer token if provided
        headers = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        ws.connect(f"wss://{server_address}/ws?clientId={client_id}", header=headers)
        print(f"Connected to WebSocket at wss://{server_address}/ws")
    except Exception as e:
        print(f"Failed to connect to WebSocket: {e}")
        raise e
    
    # Queue the prompt
    prompt_response = queue_prompt(workflow, client_id, server_address, token)
    if not prompt_response:
        print("Failed to queue prompt")
        ws.close()
        return False
    
    prompt_id = prompt_response['prompt_id']
    print(f"Queued prompt with ID: {prompt_id}")
    
    # Monitor execution and collect images
    current_node = ""
    output_images = {}
    
    try:
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        if data['node'] is None:
                            print("Execution completed!")
                            break  # Execution complete
                        else:
                            current_node = data['node']
                            print(f"Executing node: {current_node}")
                elif message['type'] == 'progress':
                    print(f"Progress: {message['data']['value']}/{message['data']['max']}")
            else:
                # Handle binary image data from SaveImageWebsocket node
                if current_node == '13':  # SaveImageWebsocket node ID
                    images_output = output_images.get(current_node, [])
                    images_output.append(out[8:])  # Skip first 8 bytes of binary header
                    output_images[current_node] = images_output
                    print("Received image data from SaveImageWebsocket")
    
    except Exception as e:
        print(f"Error during WebSocket communication: {e}")
        ws.close()
        return False
    
    # Process and save the images
    saved = False
    for node_id in output_images:
        for i, image_data in enumerate(output_images[node_id]):
            try:
                # Convert binary data to PIL Image
                image = Image.open(io.BytesIO(image_data))
                
                # Save the image
                if len(output_images[node_id]) == 1:
                    save_path = output_path
                else:
                    name, ext = os.path.splitext(output_path)
                    save_path = f"{name}_{i}{ext}"
                
                image.save(save_path)
                print(f"Saved face-swapped image to: {save_path}")
                saved = True
                
            except Exception as e:
                print(f"Error processing image: {e}")
    
    # Clean up
    ws.close()
    
    return saved

def main():
    parser = argparse.ArgumentParser(description='ComfyUI Face Swap API Client')
    parser.add_argument('input_image', help='Path to the input image (face will be replaced)')
    parser.add_argument('source_image', help='Path to the source image (face to use for replacement)')
    parser.add_argument('output_image', help='Path to save the result image')
    parser.add_argument('--server', default=SERVER_ADDRESS, 
                       help=f'ComfyUI server address (default: {SERVER_ADDRESS})')
    parser.add_argument('--token', '-t', 
                       help='Bearer token for authentication')
    
    args = parser.parse_args()
    
    # Check for token in environment variables if not provided via CLI
    token = args.token or os.getenv('COMFYUI_TOKEN') or os.getenv('WEB_TOKEN')
    
    # Validate input files
    if not os.path.exists(args.input_image):
        print(f"Error: Input image '{args.input_image}' not found")
        sys.exit(1)
    
    if not os.path.exists(args.source_image):
        print(f"Error: Source image '{args.source_image}' not found")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_image)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Starting face swap...")
    print(f"Input image: {args.input_image}")
    print(f"Source image: {args.source_image}")
    print(f"Output image: {args.output_image}")
    print(f"Server: {args.server}")
    if token:
        print(f"Authentication: Enabled (token: {token[:8]}...)")
    else:
        print("Authentication: Disabled")
    
    # Perform face swap
    success = face_swap_websocket(args.input_image, args.source_image, 
                                 args.output_image, args.server, token)
    
    if success:
        print("Face swap completed successfully!")
    else:
        print("Face swap failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
