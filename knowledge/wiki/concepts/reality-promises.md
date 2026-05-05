# Reality Promises

## Definition
**Reality Promises** is a mixed-reality concept that creates the illusion of manipulating physical objects in ways only virtuality affords, while secretly propagating virtual manipulations to physical reality through an invisible mobile robot [[sources/reality-promises]](../sources/reality-promises.md).

## Core Mechanism
The system operates on **virtual-physical decoupling illusions**, creating two levels of reality:
1. **Experiential level**: Perceived by the user, where objects can be manipulated in ways only virtuality affords (e.g., telekinesis, materialization)
2. **Physical level**: An invisible mobile robot replicates the virtual manipulations without exposing itself to the user

## Technical Architecture
- **Skynet**: Mobile manipulator robot control with inside-out tracking, full-scale navigation, and event monitoring/prediction
- **SplatiMate**: Robot-aware 3D Gaussian splatting for visually hiding the mobile robot in passthrough MR views
- **RealityGoGo**: Interaction technique for point-and-pinch selection and reach-and-drop placement across arbitrary distances

## Decoupling Modes
1. **Removal mode**: Physical object hidden, virtual object added at same pose
2. **Augmented mode**: Fully transparent virtual clone overlaid on physical object, becoming opaque during manipulation

## Demonstrated Experiences
- **MagicMake**: Materializing objects out of thin air (e.g., coconut water bottle)
- **Seamless MagicMove**: Telekinetically moving physical objects through space
- **De- and Rematerializing MagicMove**: Objects dematerializing from one location and rematerializing at another
- **Character MagicMove**: Virtual characters manipulating physical objects (e.g., bee snatching chips container)

## Design Space
Reality Promises distinguish between:
- **Intrinsic value interactions**: Require bodily contact with object (consuming, using)
- **Extrinsic value interactions**: Focus on outcome rather than tangible interaction (tidying, relocating)

## Related Concepts
- [[concepts/augmented-object-intelligence]] - Similar goal of augmenting physical objects but uses different approach (MLLMs vs. invisible robots)
- [[analyses/xr-objects-system]] - XR-Objects provides object-based AR interactions without robot mediation
- [[xr-ai-intersection]] - Broader context of XR and AI technology intersections

## Limitations
- Requires mobile manipulator robot infrastructure
- Robot must remain invisible to maintain illusion (challenging in complex scenes)
- Tight synchrony required between virtual manipulation and physical replication

---
## Sources
- [[sources/reality-promises]](../sources/reality-promises.md) - UIST 2025, DOI: 10.1145/3746059.3747660
