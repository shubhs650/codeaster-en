// shell_static: simply supported square plate, mid-surface in the XY plane (DKT/DKQ shell).
// Units: mm. Regenerate with:  gmsh -2 mesh.geo -format med -o mesh.med
// Four quadrants so that the plate centre is a mesh node (group CENTER).
a = 1000;   // side length
n = 10;     // elements per quadrant edge -> 20 x 20 QUAD4 over the plate
h = a/2;

Point(1) = {0, 0, 0};  Point(2) = {h, 0, 0};  Point(3) = {a, 0, 0};
Point(4) = {0, h, 0};  Point(5) = {h, h, 0};  Point(6) = {a, h, 0};
Point(7) = {0, a, 0};  Point(8) = {h, a, 0};  Point(9) = {a, a, 0};

// Boundary edges
Line(1) = {1, 2};  Line(2) = {2, 3};  Line(3) = {3, 6};  Line(4) = {6, 9};
Line(5) = {9, 8};  Line(6) = {8, 7};  Line(7) = {7, 4};  Line(8) = {4, 1};
// Interior lines through the centre
Line(9) = {2, 5};  Line(10) = {5, 8};  Line(11) = {4, 5};  Line(12) = {5, 6};

// Counter-clockwise loops seen from +Z, so element normals point to +Z.
Curve Loop(1) = {1, 9, -11, 8};    Plane Surface(1) = {1};
Curve Loop(2) = {2, 3, -12, -9};   Plane Surface(2) = {2};
Curve Loop(3) = {12, 4, 5, -10};   Plane Surface(3) = {3};
Curve Loop(4) = {11, 10, 6, 7};    Plane Surface(4) = {4};

Transfinite Curve {1:12} = n + 1;
Transfinite Surface {1:4};
Recombine Surface {1:4};

Physical Surface("PLATE") = {1, 2, 3, 4};
Physical Curve("EDGES") = {1:8};          // simply supported: DZ = 0
Physical Point("CENTER") = {5};           // maximum deflection
Physical Point("CORNER_A") = {1};         // in-plane rigid-body restraint DX = DY = 0
Physical Point("CORNER_B") = {3};         // in-plane rigid-body restraint DY = 0

Mesh.ElementOrder = 1;
Mesh.SaveAll = 0;
