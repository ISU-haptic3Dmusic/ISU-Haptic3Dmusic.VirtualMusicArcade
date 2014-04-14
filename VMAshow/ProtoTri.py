from H3DInterface import *
import math
import sys

# a Field class that computes the three vertices of an isosceles triangle, given
# an internal angle and a side length
class CalculateTriangleVertices( TypedField( MFVec3f, ( SFFloat, SFFloat ))):
    def update( self, event ):
        routes_in = self.getRoutesIn()
        angle = routes_in[0].getValue()
        side_length = routes_in[1].getValue()

        vertices = []

        vertices.append( Vec3f( 0, 0, 0 ) )
        vertices.append( Vec3f( side_length, 0, 0 ) )
        vertices.append( Vec3f( side_length * math.cos( angle ), side_length * math.sin( angle ), 0 ) )

        return vertices

# a Field class to get a representation of the triangle as a set of
# three "edge vectors"
class CalculateTriangleEdgeVectors( MFVec3f ):
    def update( self, event ):
        if( not event.empty() ):
            vertices = event.getValue()
            return [ vertices[1] - vertices[0],
                     vertices[2] - vertices[1],
                     vertices[0] - vertices[2] ]

        zero_vec = Vec3f( 0, 0, 0 )
        return [ zero_vec, zero_vec, zero_vec ]

# a Field class that computes the orthogonal projections of the contact point
# onto the three sides of the triangle
class CalculateProjections( TypedField( MFVec3f, ( MFVec3f, MFVec3f, MFVec3f ))):
    def update( self, event ):
        routes_in = self.getRoutesIn()
        contact_points = routes_in[0].getValue()
        edge_vectors = routes_in[1].getValue()
        vertices = routes_in[2].getValue()

        if( not routes_in[0].empty() ):
            side_a_vector = ( edge_vectors[0] ).normalizeSafe()
            side_b_vector = ( edge_vectors[1] ).normalizeSafe()
            side_c_vector = ( edge_vectors[2] ).normalizeSafe()

            # calculate contact point projection onto side a
            vector_to_project = contact_points[0] - vertices[0]
            proj_point_a = vector_to_project.dotProduct( side_a_vector ) * side_a_vector

            # calculate contact point projection onto side b
            vector_to_project = contact_points[0] - vertices[1]
            proj_point_b = vector_to_project.dotProduct( side_b_vector ) * side_b_vector
            proj_point_b = proj_point_b + vertices[1]

            # calculate contact point projection onto side c
            vector_to_project = contact_points[0] - vertices[2]
            proj_point_c = vector_to_project.dotProduct( side_c_vector ) * side_c_vector
            proj_point_c = proj_point_c + vertices[2]

            return [ proj_point_a, proj_point_b, proj_point_c ]

        # if we get to this point, contact_points is empty, so just fill the MFVec3f
        # with the right number of zero vectors
        zero_vec = Vec3f( 0, 0, 0 )
        return [ zero_vec, zero_vec, zero_vec ]

# a Field class to assemble the 'point' value for the Coordinate node that helps
# draw the projection lines
class CalculateProjectionIdxLineSetVertices( TypedField( MFVec3f, ( MFVec3f, MFVec3f ))):
    def update( self, event ):
        routes_in = self.getRoutesIn()
        contact_points = routes_in[0].getValue()
        projections = routes_in[1].getValue()

        if( not routes_in[0].empty() ):
            return [ contact_points[0], projections[0], projections[1], projections[2] ]

        zero_vec = Vec3f( 0, 0, 0 )
        return [ zero_vec, zero_vec, zero_vec, zero_vec ]

# a Field class to perform a logical OR of all elements in an MFBool
class LogicalOr( TypedField( SFBool, ( MFBool ))):
    def update( self, event ):
        if( not event.empty() ):
            bool_values = event.getValue()

            for bool_val in bool_values:
                # if any of the values in the MFBool is True,
                # return True
                if( bool_val ):
                    return True

        # if we get to this point, it means the MFBool is either empty
        # or all its elements are False, so return False
        return False

# a Field class to calculate vertices for an IndexedFaceSet that
# forms the exterior "walls" around the triangle
#
# Re-uses the results of the CalculateTriangleVertices instance
class CalculateWallVertices( MFVec3f ):
    def update( self, event ):
        if( not event.empty() ):
            tri_verts = event.getValue()

            wall_verts = []

            # first, the set of vertices that form the "top"
            # edge of the wall
            wall_verts.append( Vec3f( tri_verts[0].x, tri_verts[0].y, 0.002 ))
            wall_verts.append( Vec3f( tri_verts[1].x, tri_verts[1].y, 0.002 ))
            wall_verts.append( Vec3f( tri_verts[2].x, tri_verts[2].y, 0.002 ))

            # then, the set of vertices that form the "bottom"
            # edge of the wall
            wall_verts.append( Vec3f( tri_verts[0].x, tri_verts[0].y, 0.0001 ))
            wall_verts.append( Vec3f( tri_verts[1].x, tri_verts[1].y, 0.0001 ))
            wall_verts.append( Vec3f( tri_verts[2].x, tri_verts[2].y, 0.0001 ))

            return wall_verts

        zero_vec = Vec3f( 0, 0, 0 )
        return [ zero_vec, zero_vec, zero_vec, zero_vec, zero_vec, zero_vec ]

# a Field class to "normalize" the projections, such that the position of
# a projected point along each edge of the triangle is mapped to the range
# [0, 1]
class CalculateNormalizedProjections( TypedField( SFVec3f, ( MFVec3f, MFVec3f, MFVec3f ))):
    def update( self, event ):
        routes_in = self.getRoutesIn()
        projections = routes_in[0].getValue()
        edge_vectors = routes_in[1].getValue()
        vertices = routes_in[2].getValue()

        if( not routes_in[0].empty() ):
            norm_a = ( projections[0] - vertices[0] ).length() / edge_vectors[0].length()
            norm_b = ( projections[1] - vertices[1] ).length() / edge_vectors[1].length()
            norm_c = ( projections[2] - vertices[2] ).length() / edge_vectors[2].length()

            return Vec3f( norm_a, norm_b, norm_c )

        # fallback: return a zero vector
        return Vec3f( 0, 0, 0 )

# a Field class to calculate the incenter (the center point of the incircle)
# of the triangle.
class CalculateIncenter( TypedField( SFVec3f, ( MFVec3f, MFVec3f ))):
    def update( self, event ):
        routes_in = self.getRoutesIn()
        edge_vectors = routes_in[0].getValue()
        vertices = routes_in[1].getValue()

        if( not event.empty() ):
            # http://en.wikipedia.org/wiki/Incircle
            a = edge_vectors[1].length() # the side opposite vertex 'a'
            b = edge_vectors[2].length() # the side opposite vertex 'b'
            c = edge_vectors[0].length() # the side opposite vertex 'c'

            P = a + b + c

            incircle_xcoord = ( a * vertices[0].x + b * vertices[1].x + c * vertices[2].x ) / P
            incircle_ycoord = ( a * vertices[0].y + b * vertices[1].y + c * vertices[2].y ) / P

            return Vec3f( incircle_xcoord, incircle_ycoord, 0 )

        return Vec3f( 0, 0, 0 )

# a Field class to calculate the incircle radius
class CalculateIncircleRadius( TypedField( SFFloat, ( MFVec3f ))):
    def update( self, event ):
        if( not event.empty() ):
            edge_vectors = event.getValue()

            # http://en.wikipedia.org/wiki/Incircle
            a = edge_vectors[0].length()
            b = edge_vectors[1].length()
            c = edge_vectors[2].length()

            s = 0.5 * ( a + b + c )
            P = 2 * s

            K = math.sqrt( s * ( s - a ) * ( s - b ) * ( s - c ) )
            radius = ( 2 * K ) / P

            return radius

        return 0.0

# A helper function to calculate the 2D intersection of a ray and a line segment
#   returns a tuple ( bool, Vec2f )
#   if the bool is true, the Vec2f will contain the intersection point
#
# See:
# http://stackoverflow.com/questions/14307158/how-do-you-check-for-intersection-between-a-line-segment-and-a-line-ray-emanatin
# http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect/565282#565282
def rayToLineSegmentIsect( ray_origin, ray_direction, seg_start, seg_direction ):
    # t = ( q - p ) x s / ( r x s )
    # u = ( q - p ) x r / ( r x s )

    # p -> ray origin
    # r -> ray direction
    # q -> segment origin
    # q + s -> segment endpoint

    # define the 2D vector cross-product v x w to be ( v.x * w.y ) - ( v.y * w.x )
    # this is also the magnitude of the 3D cross-product

    # use 3D vectors to get the speed advantage from H3D's Python bindings
    p = Vec3f( ray_origin.x, ray_origin.y, 0 )
    r = Vec3f( ray_direction.x, ray_direction.y, 0 )
    q = Vec3f( seg_start.x, seg_start.y, 0 )
    s = Vec3f( seg_direction.x, seg_direction.y, 0 )

    r_cross_s_mag = r.crossProduct( s ).length()
    q_minus_p = q - p
    q_minus_p_cross_r = q_minus_p.crossProduct( r )
    seg_endpoint = q + s

    # Normally, we would need to check if r x s == 0 (to reject parallel lines)
    # and if (q - p) x s == 0 (to reject a ray that is colinear with the segment)
    #
    # However, since our ray's origin is always somewhere inside the triangle, we
    # just need to do some cross product checks against the endpoints of the line
    # that forms the edge of the triangle
    if( q_minus_p_cross_r.z >= 0 and ( seg_endpoint - p ).crossProduct( r ).z < 0 ):
        # We only need to calculate t, since the above checks guarantee that
        # u will be in the range [0, 1)
        t = q_minus_p.crossProduct( s ).length() / r_cross_s_mag
        # u = q_minus_p_cross_r.length() / r_cross_s_mag

        # No need to check that t >= 0, since we know that it must intersect
        isect_point = p + ( t * r )
        return ( True, isect_point )

    return ( False, Vec2f( 0, 0 ) )

# a Field class to calculate the intersection point of the incircle projection ray
# and an edge of the triange, as well as the normalized projections
class CalculateIncircleRayProjection( TypedField( SFVec3f, ( MFVec3f, SFVec3f, MFVec3f, MFVec3f ))):
    def __init__( self ):
        TypedField( SFVec3f, ( MFVec3f, SFVec3f, MFVec3f, MFVec3f )).__init__( self )
        self.normalizedProjections = SFVec3f()
        self.normalizedProjections.setValue( Vec3f( 0, 0, 0 ) )

    def update( self, event ):
        routes_in = self.getRoutesIn()
        contact_points = routes_in[0].getValue()
        incenter = routes_in[1].getValue()
        vertices = routes_in[2].getValue()
        edge_vectors = routes_in[3].getValue()

        if( not routes_in[0].empty() ):
            proj_ray = ( contact_points[0] - incenter ).normalizeSafe()

            ray_origin = Vec2f( incenter.x, incenter.y )
            ray_direction = Vec2f( proj_ray.x, proj_ray.y )

            # side 'a'
            seg_start = Vec2f( vertices[0].x, vertices[0].y )
            seg_direction = Vec2f( edge_vectors[0].x, edge_vectors[0].y )

            does_isect, isect_point = rayToLineSegmentIsect( ray_origin, ray_direction, seg_start, seg_direction )
            if( does_isect ):
                isect_point_vec3 = Vec3f( isect_point.x, isect_point.y, 0 )
                norm_proj = self.normalizedProjections.getValue()
                norm_proj.x = ( isect_point_vec3 - vertices[0] ).length() / edge_vectors[0].length()
                self.normalizedProjections.setValue( norm_proj )
                return isect_point_vec3

            # side 'b'
            seg_start = Vec2f( vertices[1].x, vertices[1].y )
            seg_direction = Vec2f( edge_vectors[1].x, edge_vectors[1].y )

            does_isect, isect_point = rayToLineSegmentIsect( ray_origin, ray_direction, seg_start, seg_direction )
            if( does_isect ):
                isect_point_vec3 = Vec3f( isect_point.x, isect_point.y, 0 )
                norm_proj = self.normalizedProjections.getValue()
                norm_proj.y = ( isect_point_vec3 - vertices[1] ).length() / edge_vectors[1].length()
                self.normalizedProjections.setValue( norm_proj )
                return isect_point_vec3

            # side 'c'
            seg_start = Vec2f( vertices[2].x, vertices[2].y )
            seg_direction = Vec2f( edge_vectors[2].x, edge_vectors[2].y )

            does_isect, isect_point = rayToLineSegmentIsect( ray_origin, ray_direction, seg_start, seg_direction )
            if( does_isect ):
                isect_point_vec3 = Vec3f( isect_point.x, isect_point.y, 0 )
                norm_proj = self.normalizedProjections.getValue()
                norm_proj.z = ( isect_point_vec3 - vertices[2] ).length() / edge_vectors[2].length()
                self.normalizedProjections.setValue( norm_proj )
                return isect_point_vec3

        return Vec3f( incenter.x, incenter.y, 0 )

class AssembleIncircleProjectionCoords( TypedField( MFVec3f, ( SFVec3f, SFVec3f ))):
    def update( self, event ):
        routes_in = self.getRoutesIn()
        incenter = routes_in[0].getValue()
        proj = routes_in[1].getValue()

        return [ incenter, proj ]

class ProjectionModeState( TypedField( SFInt32, ( SFString ))):
    # States (encoded as integers):
    #   ORTHO -> 0
    #   LATCHED -> 1
    #   INCIRCLE -> 2
    def __init__( self,
                  ortho_proj_coord_node,
                  incircle_proj_coord_node,
                  ortho_proj_points_field,
                  incircle_proj_points_field,
                  norm_ortho_proj_source_field,
                  norm_incircle_proj_source_field,
                  norm_proj_sink_field ):
        TypedField( SFInt32, ( SFString )).__init__( self )
        self.setValue( 0 )
        self.orthoProjCoordNode = ortho_proj_coord_node
        self.incircleProjCoordNode = incircle_proj_coord_node
        self.orthoProjPointsField = ortho_proj_points_field
        self.incircleProjPointsField = incircle_proj_points_field
        self.normOrthoProjSourceField = norm_ortho_proj_source_field
        self.normIncircleProjSourceField = norm_incircle_proj_source_field
        self.normProjSinkField = norm_proj_sink_field
        self.orthoProjPointsField.route( self.orthoProjCoordNode.point )
        self.normOrthoProjSourceField.route( self.normProjSinkField )

    def update( self, event ):
        mode_string = event.getValue()

        current_state = self.getValue()
        next_state = current_state

        if( current_state == 0 ):
            if( mode_string == "LATCHED" ):
                #print "ORTHO -> LATCHED"
                next_state = 1
            elif( mode_string == "INCIRCLE" ):
                #print "ORTHO -> INCIRCLE"
                self.orthoProjPointsField.unroute( self.orthoProjCoordNode.point )
                self.normOrthoProjSourceField.unroute( self.normProjSinkField )
                self.incircleProjPointsField.route( self.incircleProjCoordNode.point )
                self.normIncircleProjSourceField.route( self.normProjSinkField )
                next_state = 2
        elif( current_state == 1 ):
            if( mode_string == "ORTHO" ):
                #print "LATCHED -> ORTHO"
                next_state = 0
            elif( mode_string == "INCIRCLE" ):
                #print "LATCHED -> INCIRCLE"
                next_state = 2
        elif( current_state == 2 ):
            if( mode_string == "ORTHO" ):
                #print "INCIRCLE -> ORTHO"
                self.incircleProjPointsField.unroute( self.incircleProjCoordNode.point )
                self.normIncircleProjSourceField.unroute( self.normProjSinkField )
                self.orthoProjPointsField.route( self.orthoProjCoordNode.point )
                self.normOrthoProjSourceField.route( self.normProjSinkField )
                next_state = 0
            elif( mode_string == "LATCHED" ):
                #print "INCIRCLE -> LATCHED"
                next_state = 1

        return next_state

class StateBasedToggle( TypedField( SFBool, ( SFInt32 ))):
    def __init__( self, active_state ):
        TypedField( SFBool, ( SFInt32 )).__init__( self )
        self.activeState = active_state

    def update( self, event ):
        state = event.getValue()

        if( state == self.activeState ):
            return True
        else:
            return False

def initialize():
    referenced_nodes = references.getValue()

    tri_idx_face_set_node = referenced_nodes[0]
    tri_idx_face_set_coord_node = referenced_nodes[1]

    ortho_proj_line_coord_node = referenced_nodes[2]
    incircle_proj_line_coord_node = referenced_nodes[3]

    outside_wall_coord_node = referenced_nodes[4]
    outside_wall_togglegroup_node = referenced_nodes[5]
    incircle_xform_node = referenced_nodes[6]
    incircle_circle2d_node = referenced_nodes[7]

    ortho_proj_togglegroup_node = referenced_nodes[8]
    latched_proj_togglegroup_node = referenced_nodes[9]
    incircle_proj_togglegroup_node = referenced_nodes[10]

    global internalAngle
    global sideLength

    internalAngle = SFFloat()
    sideLength = SFFloat()

    # create an instance of CalculateTriangleVertices and set
    # up its routes
    global calcTriangleVertices
    calcTriangleVertices = CalculateTriangleVertices()
    internalAngle.routeNoEvent( calcTriangleVertices )
    sideLength.route( calcTriangleVertices )
    calcTriangleVertices.route( tri_idx_face_set_coord_node.point )

    # create an instance of CalculateTriangleEdgeVectors and set
    # up its routes
    global calcTriangleEdgeVectors
    calcTriangleEdgeVectors = CalculateTriangleEdgeVectors()
    calcTriangleVertices.route( calcTriangleEdgeVectors )

    # create an instance of CalculateProjections and set up
    # its routes
    global calcProjections
    calcProjections = CalculateProjections()
    tri_idx_face_set_node.contactPoint.routeNoEvent( calcProjections )
    calcTriangleEdgeVectors.routeNoEvent( calcProjections )
    calcTriangleVertices.route( calcProjections )

    # create an instance of CalculateProjectionIdxLineSetVertices and
    # set up its routes
    global calcProjectionIdxLineSetVertices
    calcProjectionIdxLineSetVertices = CalculateProjectionIdxLineSetVertices()
    tri_idx_face_set_node.contactPoint.routeNoEvent( calcProjectionIdxLineSetVertices )
    calcProjections.route( calcProjectionIdxLineSetVertices )
    #calcProjectionIdxLineSetVertices.route( ortho_proj_line_coord_node.point )

    # create an instance of CalculateWallVertices and set up routes
    global calcWallVertices
    calcWallVertices = CalculateWallVertices()
    calcTriangleVertices.route( calcWallVertices )
    calcWallVertices.route( outside_wall_coord_node.point )

    # create an instance of CalculateNormalizedProjections and set up routes
    global calcNormalizedProjections
    calcNormalizedProjections = CalculateNormalizedProjections()
    calcProjections.routeNoEvent( calcNormalizedProjections )
    calcTriangleEdgeVectors.routeNoEvent( calcNormalizedProjections )
    calcTriangleVertices.route( calcNormalizedProjections )

    # toggle the exterior wall on/off with isTouched
    global logicalOR
    logicalOR = LogicalOr()
    tri_idx_face_set_node.isTouched.route( logicalOR )
    logicalOR.route( outside_wall_togglegroup_node.graphicsOn )
    logicalOR.route( outside_wall_togglegroup_node.hapticsOn )

    # set up the incircle stuff
    global calcIncenter
    calcIncenter = CalculateIncenter()
    calcTriangleEdgeVectors.routeNoEvent( calcIncenter )
    calcTriangleVertices.routeNoEvent( calcIncenter )
    calcIncenter.route( incircle_xform_node.translation )

    global calcIncircleRadius
    calcIncircleRadius = CalculateIncircleRadius()
    calcTriangleEdgeVectors.route( calcIncircleRadius )
    calcIncircleRadius.route( incircle_circle2d_node.radius )

    # set up fields related to the incircle projection
    global calc_incircle_ray_proj
    calc_incircle_ray_proj = CalculateIncircleRayProjection()
    tri_idx_face_set_node.contactPoint.routeNoEvent( calc_incircle_ray_proj )
    calcIncenter.routeNoEvent( calc_incircle_ray_proj )
    calcTriangleVertices.routeNoEvent( calc_incircle_ray_proj )
    calcTriangleEdgeVectors.route( calc_incircle_ray_proj )

    global incircle_proj_points
    incircle_proj_points = AssembleIncircleProjectionCoords()
    calcIncenter.routeNoEvent( incircle_proj_points )
    calc_incircle_ray_proj.route( incircle_proj_points )
    #incircle_proj_points.route( incircle_proj_line_coord_node.point )

    global norm_projections
    norm_projections = SFVec3f()

    # create ProjectionModeState instance
    global projection_mode
    projection_mode = SFString()

    global projection_mode_state
    projection_mode_state = ProjectionModeState( ortho_proj_line_coord_node,
                                                 incircle_proj_line_coord_node,
                                                 calcProjectionIdxLineSetVertices,
                                                 incircle_proj_points,
                                                 calcNormalizedProjections,
                                                 calc_incircle_ray_proj.normalizedProjections,
                                                 norm_projections )
    projection_mode.route( projection_mode_state )

    # create StateBasedToggle instances
    global ortho_proj_toggle
    ortho_proj_toggle = StateBasedToggle( 0 )
    projection_mode_state.route( ortho_proj_toggle )
    ortho_proj_toggle.route( ortho_proj_togglegroup_node.graphicsOn )

    global incircle_proj_toggle
    incircle_proj_toggle = StateBasedToggle( 2 )
    projection_mode_state.route( incircle_proj_toggle )
    incircle_proj_toggle.route( incircle_proj_togglegroup_node.graphicsOn )
