# LeafyCV1.0 Final Semantic Model

- Task: binary semantic segmentation (`canopy` vs `background`)
- Architecture: U-Net
- Encoder: EfficientNet-B0
- Input: 512x512 RGB
- Input scaling: divide pixels by 255.0
- Mean/std normalization: none
- Output: one logit channel
- Sigmoid threshold: 0.5
- OpenCV binary mask: 0 = background, 255 = canopy

The bundled checkpoint is inference-only. The training dataset is not required by the runtime package.
