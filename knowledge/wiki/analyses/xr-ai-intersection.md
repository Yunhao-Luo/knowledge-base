# XR and AI Intersection

## Definition
The intersection of Extended Reality (XR) and Artificial Intelligence (AI) refers to research where these two technologies are combined to address fundamental questions in human-computer interaction, computer graphics, computer vision, and related fields.

## Background
Previously, XR and AI research happened primarily within their respective fields. However, tools like Unity3D and Keras have made both more accessible, leading to an emerging research field at their intersection [[sources/XR-AI]](../sources/XR-AI.md).

## Five Main Research Topics
Based on a scoping review of 311 papers (2017-2021) from 203 international venues, five main topics dominate the intersection:

### 1. Using AI to Create XR Worlds (28.6%)
Focuses on three approaches:
- Realistically replicating real-world environments and human representations
- Modifying real-world content for virtual contexts
- Generating entirely synthetic virtual worlds

Most work concentrates on creating realistic environments, avatars, and agents with attention to physical appearance and behavioral modeling.

### 2. Using AI to Understand Users (19.3%)
Primarily focuses on:
- Predicting VR sickness through machine learning approaches
- Predicting user characteristics like emotion and presence
- Analyzing viewport and head movement patterns

**Limitation**: Research typically adopts a performance-driven perspective rather than examining broader usability and user experience considerations.

### 3. Using AI to Support Interaction (15.4%)
Addresses:
- Gestural interaction through improved hand tracking and pose estimation
- Locomotion techniques, particularly redirected walking
- Novel interaction devices and techniques

**Gap**: Underrepresentation of haptic feedback research despite its importance in XR.

### 4. Investigating Interaction with Intelligent Virtual Agents (8.0%)
Investigates user perception of agents through:
- Perceptual experiments
- Empathy, trust, and personality modeling

**Gap**: Agent behavior is typically scripted rather than genuinely implemented through AI models.

### 5. Using XR to Support AI Research (2.3%)
Focuses on:
- Visualizing AI methods to improve understanding for non-experts
- Addressing limited training data challenges

## Critical Gaps in Current Research
[[sources/XR-AI]](../sources/XR-AI.md) identifies several critical gaps:

1. **Insufficient generative model application** - Lack of generative approaches using techniques like GANs for content creation
2. **Limited dataset diversity and generalizability** - Most research uses small sample sizes biased toward young male Western populations
3. **Underrepresentation of robustness testing** - Across different tasks and populations
4. **Minimal discussion of ethical and societal implications**
5. **Lack of theoretical and methodological guidelines** for applying AI to specific XR problems

## Research Opportunities
The review presents 13 research opportunities, emphasizing:
- Larger diverse datasets
- Cross-task validation
- Human-AI collaboration approaches
- Greater attention to societal impacts

## Methodological Context
This scoping review follows the Joanna Briggs Institute methodology for systematic scoping reviews [[sources/guidance-review]](../sources/guidance-review.md). Scoping reviews are particularly useful when a body of literature has not yet been comprehensively reviewed or exhibits complex/heterogeneous nature, serving to clarify working definitions and conceptual boundaries.

## Related Work
Existing reviews typically focus on:
- Specific use cases (e.g., medical training, surgery simulations)
- Particular aspects of XR and AI research
- Application domains rather than fundamental research questions

This scoping review differs by providing a comprehensive account of the current landscape at the intersection itself.

## See Also
- [[analyses/xr-ai-topics]] - Detailed topic breakdown from scoping review
- [[sources/XR-AI]] - Original CHI 2023 scoping review
- [[concepts/augmented-object-intelligence]] - Object-based AR interactions
- [[analyses/xr-objects-system]] - XR-Objects prototype implementation
- [[sources/guidance-review]] - Methodological guidance for scoping reviews
- [[concepts/xr-ai-intersection]] - Conceptual overview of XR-AI intersection

---
## Sources
- [[sources/XR-AI]](../sources/XR-AI.md) - CHI 2023, DOI: 10.1145/3544548.3581072
- [[sources/guidance-review]](../sources/guidance-review.md) - Joanna Briggs Institute methodology guidance
