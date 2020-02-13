#!/usr/bin/env python
#
# Copyright 2019 DFKI GmbH.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the
# following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.
import numpy as np


def intersect_ray_with_plane(normal, ray_start, ray_dir):
    '''http://en.wikipedia.org/wiki/Line-plane_intersectionl
    '''
    l0 = ray_start
    n = normal

    numerator = np.dot(-l0, n)
    denominator = np.dot(ray_dir, n)
    if denominator != 0:
        d = numerator / denominator
        intersection = l0 + ray_dir * d
        return intersection
    else:
        return None



def closestLowerValueBinarySearch(A,left,right,value,getter= lambda A,i : A[i]):   
    ''' src: from http://stackoverflow.com/questions/4257838/how-to-find-closest-value-in-sorted-array
    - left smallest index of the searched range
    - right largest index of the searched range
    - A array to be searched
    - parameter is an optional lambda function for accessing the array
    - returns a tuple (index of lower bound in the array, flag: 0 = exact value was found, 1 = lower bound was returned, 2 = value is lower than the minimum in the array and the minimum index was returned, 3= value exceeds the array and the maximum index was returned)
    '''

    #result =(-1,False)
    delta = int(right -left)
    #print delta
    if (delta> 1) :#or (left ==0 and (delta> 0) ):# or (right == len(A)-1 and ()):#test if there are more than two elements to explore
        iMid = int(left+((right-left)/2))
        testValue = getter(A,iMid)
        #print "getter",testValue
        if testValue>value:
            #print "right"
            return closestLowerValueBinarySearch(A, left, iMid, value,getter)
        elif testValue<value:
            #print "left"
            return closestLowerValueBinarySearch(A, iMid, right, value,getter)
        else:
            #print "done"
            return (iMid,0)
    else:#always return the lowest closest value if no value was found, see flags for the cases
        leftValue = getter(A,left)
        rightValue = getter(A,right)
        if value >= leftValue:
            if value <= rightValue:
                return (left,1)
            else:
                return (right,2)
        else:
            return(left,3)