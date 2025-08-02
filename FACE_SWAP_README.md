# ComfyUI Face Swap API Client

A simple Python program to perform face swapping using the ComfyUI API based on the provided workflow.

## Prerequisites

1. **ComfyUI Server**: Make sure you have ComfyUI running locally or on a server
   - Default local address: `127.0.0.1:8188`
   - For remote servers, use the appropriate IP address

2. **Python Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

3. **ComfyUI Extensions**: Ensure you have the ReActor face swap extension installed in ComfyUI
   - The workflow uses `ReActorFaceSwap` node which requires the ComfyUI-ReActor extension

## Usage

### Basic Usage
```bash
python face_swap_api.py input_image.jpg source_image.jpg output_image.jpg
```

### With Authentication
```bash
python face_swap_api.py input_image.jpg source_image.jpg output_image.jpg --token your_bearer_token
```

### With Custom Server and Authentication
```bash
python face_swap_api.py input_image.jpg source_image.jpg output_image.jpg --server 192.168.1.100:8188 --token your_bearer_token
```

### Using Environment Variables for Authentication
```bash
export COMFYUI_TOKEN=your_bearer_token
# OR
export WEB_TOKEN=your_bearer_token
python face_swap_api.py input_image.jpg source_image.jpg output_image.jpg
```

### Arguments
- `input_image`: Path to the input image (the face in this image will be replaced)
- `source_image`: Path to the source image (the face from this image will be used for replacement)
- `output_image`: Path where the result image will be saved
- `--server`: ComfyUI server address (optional, defaults to comfyui.zrok.lcas.group)
- `--token`, `-t`: Bearer token for authentication (optional)

### Authentication
The program supports Bearer token authentication for accessing protected ComfyUI servers:

1. **Command Line Arguments**: Use `--token` flag
2. **Environment Variables**: Set `COMFYUI_TOKEN` or `WEB_TOKEN`
3. **No Authentication**: If no token is provided, requests are sent without authentication

The token is sent in the `Authorization: Bearer <token>` header with each request.

## How it Works

1. **Image Upload**: The program uploads your input images to ComfyUI via the `/upload/image` API endpoint
2. **Workflow Execution**: It sends a face swap workflow to ComfyUI via WebSocket API
3. **Real-time Monitoring**: Monitors the execution progress through WebSocket messages
4. **Image Retrieval**: Receives the result image directly through WebSocket (SaveImageWebsocket node)
5. **Output Saving**: Saves the face-swapped result to your specified output path

## Workflow Details

The program uses a workflow that includes:
- **LoadImage nodes** (3, 4): Load the input and source images
- **ImageScaleBy nodes** (9, 10): Scale images to 25% for processing efficiency
- **ReActorFaceSwap node** (2): Perform the actual face swapping
- **SaveImageWebsocket node** (13): Stream the result back via WebSocket

## Configuration

The program automatically uploads images via ComfyUI's API, so no manual file copying is required. The images are uploaded to ComfyUI's temporary storage and referenced in the workflow.

## Troubleshooting

1. **Connection Error**: Make sure ComfyUI is running and accessible at the specified address
2. **Authentication Error (401)**: Check your bearer token
3. **Missing Models**: Ensure you have the required models for ReActor:
   - `inswapper_128.onnx`
   - `YOLOv5l`
   - `GFPGANv1.3.pth`
4. **Permission Error**: Make sure the script has write access to the output directory
5. **Import Error**: Install missing dependencies with `pip install -r requirements.txt`

## Example

```bash
# Example face swap with authentication
python face_swap_api.py person1.jpg person2.jpg result.jpg --token abc123def456

# This will:
# 1. Take the face from person2.jpg
# 2. Replace the face in person1.jpg with it
# 3. Save the result as result.jpg
# 4. Use the provided token for authentication
```

## Based on Tutorial

This implementation follows the guide from: https://medium.com/@next.trail.tech/how-to-use-comfyui-api-with-python-a-complete-guide-f786da157d37
