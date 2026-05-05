# Reality Promises: Virtual-Physical Decoupling Illusions in Mixed Reality

## Publication Information
- **Title**: Reality Promises: Virtual-Physical Decoupling Illusions in Mixed Reality via Invisible Mobile Robots
- **Conference**: Proceedings of the 38th Annual ACM Symposium on User Interface Software and Technology (UIST 2025)
- **DOI**: https://dl.acm.org/doi/10.1145/3746059.3747660
- **Published**: 2025

## Abstract Summary
Reality Promises is a mixed-reality system that creates the illusion of manipulating physical objects in ways only virtuality affords, while secretly propagating virtual manipulations to physical reality through an invisible mobile robot. The system decouples virtual modes of manipulation from physical mode, creating two levels of reality: experiential (perceived by user) and physical (actual robot replication).

## Core Concept
The system branches the user's perception of physical reality into a "promised reality" where objects can be manipulated virtually, while an invisible mobile robot concurrently performs the physical manipulation without revealing itself. The illusion is resolved once the manipulatory effect is physically fully replicated.

## Technical Components
- **Skynet**: Mobile manipulator robot control system with inside-out tracking, full-scale navigation, and event monitoring/prediction
- **SplatiMate**: On-device 3D Gaussian splatting system for robot-aware visualization that hides the robot from user view
- **RealityGoGo**: Interaction technique enabling point-and-pinch selection and reach-and-drop placement across arbitrary distances

## Demonstrated Experiences
1. **MagicMake**: Materializing objects out of thin air (e.g., coconut water bottle)
2. **Seamless MagicMove**: Telekinetically moving physical objects through space
3. **De- and Rematerializing MagicMove**: Objects dematerializing from one location and rematerializing at another
4. **Character MagicMove**: Virtual characters (e.g., bee) manipulating physical objects

## Key Contributions
- Novel concept and design space of Reality Promises for virtual-physical decoupling illusions
- Three MagicMove experiences and one MagicMake end-to-end illusionary experience
- On-device & standalone 3D Gaussian splatting system (SplatiMate)
- MR-specific object selection and placement interaction technique (RealityGoGo)

## Related Work Context
This work differs from prior VR/MR divergence research by:
- Maximally preserving physical space experience while diverging only when needed for illusion
- Using robot-aware 3D Gaussian splatting for passthrough MR (not found in VR works)
- Enabling end-to-end illusionary user experiences with substitution of object motion causes
- Room-scale operation rather than table-top scale
- Tight interaction synchrony requiring minute-ahead prediction of robotic actions

## See Also
- [[concepts/augmented-object-intelligence]] - Related concept of augmenting physical objects with digital intelligence
- [[analyses/xr-objects-system]] - XR-Objects system for object-based AR interactions
- [[xr-ai-intersection]] - Broader context of XR and AI technology intersections

---
## Sources
- [[Reality Promises paper]](../sources/reality-promises.md) - UIST 2025, DOI: 10.1145/3746059.3747660
