# Semantic Reality: Interactive Context-Aware Visualization of Inter-Object Relationships in Augmented Reality

## Publication Information
- **Title**: Semantic Reality: Interactive Context-Aware Visualization of Inter-Object Relationships in Augmented Reality
- **Authors**: Xiaoan Liu, Eric J Gonzalez, Nels Numan, Andrea Colaço, Lucy Abramyan, Chen Zhu-Tian, Ryo Suzuki, Mar Gonzalez-Franco (Google)
- **Published**: 2026 (arXiv preprint)
- **Source**: https://arxiv.org/html/2604.05265v1

## Abstract Summary
Semantic Reality is an AR system focused on surfacing inter-object connectivity and making it interactive. It maintains a persistent model of objects around the user and their relationships using multimodal reasoning, spatial anchoring, and physical action recognition. Connections are visualized in-situ to highlight compatibility, reveal next steps, and reduce ambiguity during tasks.

## Core Concept
The system maintains a dynamic **semantic graph** where nodes are detected physical objects and edges are typed inter-object relations. This connectivity-centered substrate allows the AI to refer to concrete entities and links, while AR renders unambiguous in-situ overlays grounded in the user's environment rather than abstract text.

## Relation Taxonomy (8 Types)
The system organizes connections into two categories:

### Descriptive Relations
- **Spatial**: Topological or metric configuration (on, in, near)
- **Structural**: Part-whole relationships (screw part-of bracket)
- **Similarity**: Shared attributes or roles across objects
- **Comparison**: Differences between alternatives for decision making

### Prescriptive Relations
- **Affordance**: One entity can act upon another (knife acts-on garlic)
- **Compatibility**: Whether entities fit or function together with constraints
- **Procedural**: Step ordering and parallelism opportunities
- **Causality**: Preconditions and effects (drilling pilot hole enables fastening)

## Technical Architecture
- **Object Detection**: Open-vocabulary 2D detections using Gemini 2.5 Flash multimodal model
- **Spatial Anchoring**: Raycasting through 2D regions into live scene mesh for 3D world coordinates
- **AR Runtime**: Unity targeting visionOS with PolySpatial bridging to RealityKit
- **Context Windows**: Active reasoning context combining user-selected nodes, recently manipulated items, and voice-requested objects
- **User Node**: The user is represented as a node with edges capturing embodied interactions (holding, pointing, arranging)

## Interaction Techniques
- Gaze-and-pinch multi-selection for object nomination
- Voice requests to specify operations or constraints
- Embodied gestures (grabbing, bringing objects together)
- Real-time updates to semantic graph based on user actions

## Evaluations
1. **Exploratory Study**: Within-subjects comparison to single-object baseline showed clearer inter-object understanding and higher engagement/satisfaction without increased task load
2. **Scenario Benchmarking**: Compared against unaided real world, YouTube, chat assistant, and single-object XR baseline; characterized when connectivity aids planning, disambiguation, and safety

## Key Contributions
- Connectivity-centered substrate formalized as dynamic scene-anchored semantic graph
- System coupling open-vocabulary detection, world anchoring, and constrained MLLM reasoning
- Interaction techniques for steering connectivity through multi-selection, voice, and gestures
- Two evaluations indicating improved relation clarity without added task load

## See Also
- [[concepts/augmented-object-intelligence]] - Related AOI concept focusing on single-object intelligence
- [[analyses/xr-objects-system]] - XR-Objects system for object-based AR interactions
- [[sources/XR-AI]] - CHI 2023 scoping review on XR and AI

---
## Sources
- [[Semantic Reality paper]](../sources/semantic-reality.md) - arXiv 2026 preprint
