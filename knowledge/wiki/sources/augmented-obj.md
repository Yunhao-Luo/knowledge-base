# Augmented Object Intelligence with XR-Objects

## Source Information
- **Title**: Augmented Object Intelligence with XR-Objects | Proceedings of the 37th Annual ACM Symposium on User Interface Software and Technology
- **Authors**: Karan Ahuja, Sujeath Pareddy, Robert Xiao, Mayank Goel, Chris Harrison
- **Published**: UIST 2024 (Proceedings)
- **DOI**: https://dl.acm.org/doi/10.1145/3654777.3676379
- **Date Created**: 2026-05-04

## Abstract Summary
This paper explores Augmented Object Intelligence (AOI), an interaction paradigm that blurs lines between digital and physical by equipping real-world objects with interactive capabilities. The system uses real-time object segmentation, classification, and Multimodal Large Language Models (MLLMs) to enable context-aware interactions without pre-registration.

## Key Contributions
1. Defines the AOI concept and its advantages over traditional AI assistants
2. Details XR-Objects open-source system design and implementation
3. Demonstrates versatility through use cases and user study

## Technical Approach
- **Object Detection**: MediaPipe for real-time 2D bounding boxes
- **Spatial Anchoring**: Depth mapping and raycasting to convert 2D locations to 3D world coordinates
- **Semantic Understanding**: MLLMs retrieve detailed information (specifications, pricing, nutritional data)
- **Interface**: World-space UI with semi-transparent spheres that expand into context menus

## User Study Results
- **Participants**: 8 users in simulated grocery shopping and home scenarios
- **Performance**: XR-Objects completed tasks ~24% faster than Chatbot (217s vs 286s)
- **Satisfaction**: Higher satisfaction with XR-Objects for information retrieval and object comparison
- **Preference**: Stronger preference for headset-based deployment over traditional chatbot interfaces

## Contextual Background
This work builds on prior research in:
- Spatially-anchored AR interfaces (LightAnchors 2019)
- Tangible bits and seamless physical-digital interfaces (Ishii et al.)
- Cross-reality systems surveys (Auda et al. 2023)

## Applications
- Cooking: nutritional info, allergen warnings, spatial timers
- Retail: product comparison, allergen filtering
- Education: contextual learning content on physical objects
- Smart home control

## Limitations
- Current commercial headset camera access constraints
- Requires open-source implementation guidance for future hardware iterations

## See Also
- [[concepts/augmented-object-intelligence]] - Core AOI concept
- [[analyses/xr-objects-system]] - XR-Objects system details
- [[xr-ai-intersection]] - Broader XR-AI intersection context
