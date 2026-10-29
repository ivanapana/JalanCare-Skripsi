Pretrained privacy models, separate from Ivana's pothole model.

Face: OpenCV Zoo YuNet face_detection_yunet_2023mar.onnx (MIT, notice included).
Source pinned to opencv/opencv_zoo d4938dfc9d4ec5d098bfa33e98b3f3345a236586 on Hugging Face.
Plate: joker5914/yolov8n-license-plate best.onnx, revision 8286762929bd4b111a19186f2a05e0a5940b6088 (model card AGPL-3.0, license text included).
https://huggingface.co/joker5914/yolov8n-license-plate
SHA256, sizes and source URLs: MODEL_PROVENANCE.json.

These are not trained by Ivana. They run locally using OpenCV ONNX inference, without OCR, upload to external inference APIs, or additional training.
Do not replace best_potholes.pt. Test faces and Indonesian licence plates in the intended camera conditions; no universal recall guarantee.
