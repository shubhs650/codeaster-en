// modal: 3D cantilever beam, rectangular section, quadratic hexahedra (HEXA20).
// Units: mm. Regenerate with:  gmsh -3 mesh.geo -format med -o mesh.med
// Axis X (length L), width b along Y, depth h along Z.
L = 400;  b = 20;  h = 10;
nx = 80;  ny = 4;  nz = 2;   // 5 mm hexahedra

Point(1) = {0, 0, 0};  Point(2) = {0, b, 0};  Point(3) = {0, b, h};  Point(4) = {0, 0, h};
Line(1) = {1, 2};  Line(2) = {2, 3};  Line(3) = {3, 4};  Line(4) = {4, 1};
Curve Loop(1) = {1, 2, 3, 4};  Plane Surface(1) = {1};
Transfinite Curve {1, 3} = ny + 1;
Transfinite Curve {2, 4} = nz + 1;
Transfinite Surface {1};
Recombine Surface {1};
ext[] = Extrude {L, 0, 0} { Surface{1}; Layers{nx}; Recombine; };
// ext[0] = end face at X = L, ext[1] = volume

Physical Volume("BEAM") = {ext[1]};
Physical Surface("CLAMP") = {1};      // X = 0, all DOF fixed
Physical Surface("TIP") = {ext[0]};   // X = L, free end

Mesh.ElementOrder = 2;
Mesh.SecondOrderIncomplete = 1;       // 20-node serendipity hexahedra
Mesh.SaveAll = 0;
