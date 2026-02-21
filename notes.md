
# Meta goals:

Consider this as a broad (masterplan-like) mind map, so we can develop smaller features or sub-modules.  
This project is a smaller structural module of a broader integrted building science tool. The tool will focus on structural, thermal and maybe acoustic problem solving with a cental model maybe leveraging a BHOM like datascheme to create our database maybe even compas_model https://bhom.xyz/documentation/ 

Imagine this database not as an all emcompassing one. but a system that is streamlineed at this macro scale based on factor like location>>weather>>building codes, etc. 

So a change in one sub-dicipline like  thermal ascpect will show what is the impact on the structural ascpect as it is all integrated within the single central model. 

Ofcourse, building in real life are designed and engineered in stages. so we could have LOD like schemes and workflows to have access to specific workflows. 

The following is one of the submodules under structures for conceptual stages (LOD). 

# What is the MVP scope?
Since the premise of this research is to create a transtypological structural morphology engine which is not limited in its initial bias of creation, id say our mvp would scope across types like Trusses, Tensegrities, and Geodesic Gridshells. 

## Grammar engine:
if the grammar based generative method is embeded with not only adding and removing elements (node, edges and faces) but is empowered with adding restrains to its nodes then we are able to control the static and kinematic attributes of the structure. 

## Analytical enginer:
Using graphic statics as an analysis engine we are able to not just measure the forces and stress within the members but also determine the determinacy of structures as we are building the structure piece by piece. Refer the pdf: The Geometry of Equilibrium_ James Clerk Maxwell, to extract meaning elements that can be applied to this research project. Use this a bible for this poject. 

## Feasibility 
The feasibility filters which could define detailed measures of control like 
1. Reduce the material quantity (which would rely on the analytical engine to provide the load path and use the Maxwell load path theorem to reduce overall length of force vectors)
2. Scaffold free construction could be a feasibility criteria. In this case,  rigidity therory is used to create a sequence of construction like generative method while tweaking degrees of freedom to move from pin-jointed trusses to rigid beams at a specific time step of generation and back to a fully pin jointed spatial structure in the end. 

# Preferred tech stack?
Lets use compas python framework for this along with its viewer for now in this prototyping phase. But eventually, I want the core logic to be decoupled so that we can deply it on web or rhino or as a standalone tool.
We will use the compas eco system for needs based usage.  For eg, in this structural conceptual generative engine, we'd need algorithms for graphs/networks/meshes for the geometric representation, one of the graphic static packages from one of the relavent compas_3gs or compas_ags

# Success criteria for v1?
Adhereing to the feasibility creiteria using automatic penalisation and user feedback


