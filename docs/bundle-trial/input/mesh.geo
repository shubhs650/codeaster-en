// Quarter of a 200 x 100 x 10 mm steel plate with a central hole of radius 10 mm.
// Quarter model: X >= 0, Y >= 0 relative to the hole center; full thickness Z = 0..10.
// Units: mm. Regenerate with:  gmsh -3 mesh.geo -format med -o mesh.med
// Physical groups become MED groups read by run.comm (LIRE_MAILLAGE).
SetFactory("OpenCASCADE");

L = 100;  W = 50;  T = 10;   // half length (X), half width (Y), thickness (Z)
R = 10;                      // hole radius
e = 1e-3;                    // bounding-box tolerance

Box(1) = {0, 0, 0, L, W, T};
Cylinder(2) = {0, 0, -1, 0, 0, T + 2, R};
BooleanDifference(10) = { Volume{1}; Delete; }{ Volume{2}; Delete; };

symx()  = Surface In BoundingBox{-e, -e, -e, e, W+e, T+e};          // X = 0 cut plane
symy()  = Surface In BoundingBox{-e, -e, -e, L+e, e, T+e};          // Y = 0 cut plane
load()  = Surface In BoundingBox{L-e, -e, -e, L+e, W+e, T+e};       // X = 100 end face
sidey() = Surface In BoundingBox{-e, W-e, -e, L+e, W+e, T+e};       // Y = 50 free edge face
bot()   = Surface In BoundingBox{-e, -e, -e, L+e, W+e, e};          // Z = 0 face
top()   = Surface In BoundingBox{-e, -e, T-e, L+e, W+e, T+e};       // Z = 10 face
hole()  = Surface In BoundingBox{-e, -e, -e, R+e, R+e, T+e};        // hole surface

Physical Volume("PLATE") = {10};
Physical Surface("SYM_X") = {symx()};     // symmetry: DX = 0
Physical Surface("SYM_Y") = {symy()};     // symmetry: DY = 0
Physical Surface("LOAD") = {load()};      // traction 50 MPa in +X
Physical Surface("SIDE_Y") = {sidey()};   // free; used to locate the Z support node
Physical Surface("BOTTOM") = {bot()};     // free; used to locate the Z support node
Physical Surface("TOP") = {top()};        // free
Physical Surface("HOLE") = {hole()};      // free (stress concentration)

Mesh.MeshSizeMin = 1.0;
Mesh.MeshSizeMax = 6.0;
// Refine around the hole.
Field[1] = Distance;  Field[1].SurfacesList = {hole()};
Field[2] = Threshold; Field[2].InField = 1;
Field[2].SizeMin = 1.0; Field[2].SizeMax = 6.0; Field[2].DistMin = 2; Field[2].DistMax = 40;
Background Field = 2;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeFromPoints = 0;
Mesh.ElementOrder = 2;   // TETRA10: linear tetrahedra are too stiff for a stress concentration
Mesh.Optimize = 1;
Mesh.SaveAll = 0;
