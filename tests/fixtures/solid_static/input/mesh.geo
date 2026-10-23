// solid_static: short cylindrical shell with one radial nozzle (3D, linear tetrahedra).
// Units: mm. Regenerate with:  gmsh -3 mesh.geo -format med -o mesh.med
// Physical groups become MED groups read by run.comm (LIRE_MAILLAGE).
SetFactory("OpenCASCADE");

Ri = 100;  Ro = 120;  H = 300;     // shell inner/outer radius, height (axis = Z)
ri = 25;   ro = 35;   Ln = 220;    // nozzle bore/outer radius, end position on +X
Zn = H/2;                          // nozzle axis height
e  = 1e-3;                         // bounding-box tolerance

Cylinder(1) = {0, 0, 0, 0, 0, H, Ro};
Cylinder(2) = {0, 0, Zn, Ln, 0, 0, ro};
Cylinder(3) = {0, 0, 0, 0, 0, H, Ri};
Cylinder(4) = {0, 0, Zn, Ln, 0, 0, ri};
outer() = BooleanUnion{ Volume{1}; Delete; }{ Volume{2}; Delete; };
BooleanDifference(10) = { Volume{outer()}; Delete; }{ Volume{3, 4}; Delete; };

base()  = Surface In BoundingBox{-Ro-e, -Ro-e, -e, Ro+e, Ro+e, e};
top()   = Surface In BoundingBox{-Ro-e, -Ro-e, H-e, Ro+e, Ro+e, H+e};
nend()  = Surface In BoundingBox{Ln-e, -ro-e, Zn-ro-e, Ln+e, ro+e, Zn+ro+e};
wall()  = Surface In BoundingBox{-Ri-e, -Ri-e, -e, Ri+e, Ri+e, H+e};
bore()  = Surface In BoundingBox{0, -ri-e, Zn-ri-e, Ln+e, ri+e, Zn+ri+e};

Physical Volume("SOLID") = {10};
Physical Surface("BASE") = {base()};        // fixed (all DOF)
Physical Surface("TOP") = {top()};          // free
Physical Surface("NOZ_END") = {nend()};     // free, open nozzle end
Physical Surface("P_SHELL") = {wall()};     // internal pressure, shell inner wall
Physical Surface("P_NOZZLE") = {bore()};    // internal pressure, nozzle bore

Mesh.MeshSizeMin = 6;
Mesh.MeshSizeMax = 14;
// Refine around the shell/nozzle junction.
Field[1] = Distance;  Field[1].SurfacesList = {bore()};
Field[2] = Threshold; Field[2].InField = 1;
Field[2].SizeMin = 6; Field[2].SizeMax = 14; Field[2].DistMin = 10; Field[2].DistMax = 60;
Background Field = 2;
Mesh.MeshSizeExtendFromBoundary = 0;
Mesh.MeshSizeFromPoints = 0;
Mesh.ElementOrder = 1;
Mesh.Optimize = 1;
Mesh.SaveAll = 0;
