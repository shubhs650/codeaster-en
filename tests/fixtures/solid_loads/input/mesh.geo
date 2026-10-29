// solid_loads: steel block with a remote load, a spring, gravity, rotation and water pressure.
// Units: mm. Regenerate with:  gmsh -3 mesh.geo -format med -o mesh.med
// Block X 0..200, Y 0..100, Z 0..100, linear hexahedra (HEXA8) of 12.5 mm. The base surface is
// four rectangles and the extrusion has two steps, so (200, 50, 50) is a geometry vertex: the
// spring SPRING (one SEG2) runs from it to a ground node at (250, 50, 50). The remote point
// MASTER (one POI1) at (100, 50, 200) is not connected to the block.
// SEG2 and POI1 need a first-order mesh, hence HEXA8 (the checks are load sums).
Lx = 200;  Ly = 100;  Lz = 100;
n = 8;      // elements per 100 mm

Point(1) = {0, 0, 0};     Point(2) = {Lx/2, 0, 0};     Point(3) = {Lx, 0, 0};
Point(4) = {0, Ly/2, 0};  Point(5) = {Lx/2, Ly/2, 0};  Point(6) = {Lx, Ly/2, 0};
Point(7) = {0, Ly, 0};    Point(8) = {Lx/2, Ly, 0};    Point(9) = {Lx, Ly, 0};
Line(1) = {1, 2};  Line(2) = {2, 3};  Line(3) = {4, 5};  Line(4) = {5, 6};
Line(5) = {7, 8};  Line(6) = {8, 9};
Line(7) = {1, 4};  Line(8) = {4, 7};  Line(9) = {2, 5};  Line(10) = {5, 8};
Line(11) = {3, 6}; Line(12) = {6, 9};
Curve Loop(1) = {1, 9, -3, -7};   Plane Surface(1) = {1};
Curve Loop(2) = {2, 11, -4, -9};  Plane Surface(2) = {2};
Curve Loop(3) = {3, 10, -5, -8};  Plane Surface(3) = {3};
Curve Loop(4) = {4, 12, -6, -10}; Plane Surface(4) = {4};
Transfinite Curve {1:6} = n + 1;
Transfinite Curve {7:12} = n/2 + 1;
Transfinite Surface {1:4};
Recombine Surface {1:4};

low[] = Extrude {0, 0, Lz/2} { Surface{1:4}; Layers{n/2}; Recombine; };
high[] = Extrude {0, 0, Lz/2} { Surface{low[0], low[6], low[12], low[18]}; Layers{n/2}; Recombine; };

e = 1e-3;   // bounding-box tolerance, so the groups do not depend on entity numbering
attach[] = Point In BoundingBox {Lx - e, Ly/2 - e, Lz/2 - e, Lx + e, Ly/2 + e, Lz/2 + e};
Point(1000) = {Lx + 50, Ly/2, Lz/2};
Point(1001) = {Lx/2, Ly/2, 2 * Lz};
Line(1000) = {attach[0], 1000};
Transfinite Curve {1000} = 2;

Physical Volume("BLOCK") = Volume In BoundingBox {-e, -e, -e, Lx + e, Ly + e, Lz + e};
Physical Surface("BASE") = Surface In BoundingBox {-e, -e, -e, Lx + e, Ly + e, e};      // Z = 0, clamped
Physical Surface("WET") = Surface In BoundingBox {-e, -e, -e, Lx + e, e, Lz + e};       // Y = 0, water side
Physical Surface("TOP") = Surface In BoundingBox {-e, -e, Lz - e, Lx + e, Ly + e, Lz + e};  // Z = 100, remote load
Physical Line("SPRING") = {1000};
Physical Point("MASTER") = {1001};

Mesh.ElementOrder = 1;
Mesh.SaveAll = 0;
