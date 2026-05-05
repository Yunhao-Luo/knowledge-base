# XR-Objects System

## Overview
**XR-Objects** is an open-source prototype system that implements the Augmented Object Intelligence (AOI) concept, providing a platform for users to engage with their physical environment in contextually relevant ways using object-based context menus [[sources/augmented-obj]](../sources/augmented-obj.md).

## Architecture

### Detection Pipeline
1. **MediaPipe**: Real-time 2D bounding box detection and classification
2. **Depth Mapping**: Converts 2D locations into 3D world coordinates via raycasting
3. **Spatial Anchoring**: Precise positioning of digital content relative to physical objects

### Semantic Layer
- **Multimodal LLM Integration**: Each detected object couples with a multimodal language model
- **Information Retrieval**: Accesses detailed semantic information beyond basic classification (product specs, pricing, nutritional data)
- **Action Execution**: Enables querying for details or executing tasks directly from objects

## User Interface Design

### Visual Elements
- **Semi-transparent spheres**: Indicate interactable objects in world space
- **Context menus**: Expand upon user selection with organized actions
- **World-space UI**: Maintains spatial consistency with physical environment

### Interaction Categories
The system implements seven actions across four categories:
1. **Information retrieval**: Query object details and specifications
2. **Object comparison**: Compare multiple detected objects
3. **Sharing capabilities**: Share information about objects
4. **Anchoring widgets**: Spatial timers, notes, and other persistent elements [[sources/augmented-obj]](../sources/augmented-obj.md)

### Input Methods
- Voice interaction support
- Touch interaction support
- Adapts to user preferences and contextual requirements

## Use Cases Demonstrated

### Cooking Scenarios
- Nutritional information display
- Allergen warnings
- Spatially anchored timers

### Retail Applications
- Rapid product comparison
- Allergen filtering
- Price information access

### Education
- Contextual learning content on physical objects
- Interactive educational materials

### Smart Home Control
- Device interaction through physical objects
- Home automation commands

## Performance Metrics
User study with 8 participants in simulated grocery shopping and home scenarios:
- **Task completion time**: 217 seconds (XR-Objects) vs 286 seconds (Chatbot)
- **Improvement**: ~24% faster with XR-Objects
- **Satisfaction**: Higher scores for information retrieval and object comparison tasks [[sources/augmented-obj]](../sources/augmented-obj.md)

## Open Source Status
The system provides open-source implementation guidance for future hardware iterations, addressing current technical constraints with commercial headsets regarding camera access [[sources/augmented-obj]](../sources/augmented-obj.md).

## See Also
- [[concepts/augmented-object-intelligence]] - Core AOI concept
- [[sources/augmented-obj]] - Original source paper
- [[xr-ai-intersection]] - Broader XR-AI intersection context
- [[concepts/reality-promises]] - Alternative approach using invisible robots for virtual-physical manipulation
- [[sources/semantic-reality]] - Related work on inter-object relationship visualization in AR
