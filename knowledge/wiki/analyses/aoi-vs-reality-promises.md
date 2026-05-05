# AOI vs Reality Promises

## Overview
This page compares two related but distinct approaches to augmenting physical objects with digital intelligence in mixed reality contexts.

## Augmented Object Intelligence (AOI)
**Core Approach**: Equips real-world objects with the ability to interact as if they were digital entities using computer vision and multimodal language models [[concepts/augmented-object-intelligence]](../concepts/augmented-object-intelligence.md).

### Key Technologies
- **MediaPipe**: Real-time 2D bounding box detection and classification
- **Depth Mapping**: Converts 2D locations into 3D world coordinates via raycasting
- **Multimodal LLMs**: Provide semantic understanding beyond basic classification
- **Spatial Anchoring**: Precise positioning of digital content relative to physical objects

### Implementation
- **XR-Objects**: Open-source prototype system implementing AOI [[analyses/xr-objects-system]](../analyses/xr-objects-system.md)
- **Interface**: World-space UI with semi-transparent spheres and context menus
- **Interaction**: Voice, touch, and spatial selection

### Advantages
- No robot infrastructure required
- Works with existing commercial headsets
- Direct object-based interaction without navigation overhead
- 24% faster task completion in user studies [[augmented-obj]](../sources/augmented-obj.md)

## Reality Promises
**Core Approach**: Creates illusions of manipulating physical objects in ways only virtuality affords, while secretly propagating virtual manipulations to physical reality through an invisible mobile robot [[concepts/reality-promises]](../concepts/reality-promises.md).

### Key Technologies
- **Skynet**: Mobile manipulator robot control with inside-out tracking
- **SplatiMate**: Robot-aware 3D Gaussian splatting for hiding the robot
- **RealityGoGo**: Interaction technique for point-and-pinch selection and reach-and-drop placement

### Implementation
- **MagicMake**: Materializing objects out of thin air
- **Seamless MagicMove**: Telekinetically moving physical objects
- **De- and Rematerializing MagicMove**: Objects dematerializing and rematerializing at different locations
- **Character MagicMove**: Virtual characters manipulating physical objects

### Advantages
- Enables virtual manipulation modes impossible in pure AR
- Preserves physical space experience while diverging only when needed
- End-to-end illusionary user experiences

## Key Differences

| Aspect | AOI (XR-Objects) | Reality Promises |
|--------|------------------|------------------|
| **Physical Mediation** | None - direct digital overlay | Invisible robot mediates physical changes |
| **Infrastructure** | Commercial headsets only | Mobile manipulator robot required |
| **Interaction Mode** | Information retrieval, comparison | Physical manipulation illusions |
| **Illusion Type** | Digital augmentation | Virtual-physical decoupling |
| **Complexity** | Lower - camera-based detection | Higher - robot control and synchronization |

## Use Case Comparison

### AOI Strengths
- Cooking: Nutritional info, allergen warnings, spatial timers
- Retail: Product comparison, price information
- Education: Contextual learning on physical objects
- Smart home: Device interaction through physical objects

### Reality Promises Strengths
- MagicMake: Materializing objects (e.g., coconut water bottle)
- Seamless MagicMove: Telekinetically moving objects through space
- De- and Rematerializing: Objects appearing/disappearing at different locations
- Character interactions: Virtual characters manipulating physical objects

## Research Gaps
Both approaches share some gaps identified in XR-AI intersection research:
- Limited dataset diversity and generalizability [[xr-ai-intersection]](../analyses/xr-ai-intersection.md)
- Underrepresentation of robustness testing across populations
- Minimal discussion of ethical and societal implications
- Lack of theoretical and methodological guidelines for specific XR problems

## Future Directions
1. **Hybrid approaches**: Combining AOI's accessibility with Reality Promises' manipulation capabilities
2. **Cross-validation**: Larger diverse datasets for both systems
3. **Human-AI collaboration**: Better integration of AI agents in both paradigms
4. **Ethical frameworks**: Addressing societal impacts of object augmentation

## See Also
- [[concepts/augmented-object-intelligence]] - AOI core concept
- [[concepts/reality-promises]] - Reality Promises core concept
- [[analyses/xr-objects-system]] - XR-Objects implementation details
- [[xr-ai-intersection]] - Broader XR-AI intersection context
