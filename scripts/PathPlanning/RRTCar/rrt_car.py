#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@brief: Path Planning Sample Code with RRT for car like robot.

@author: AtsushiSakai(@Atsushi_twi)

@license: MIT

"""

import random
import math
import copy
import numpy as np
import dubins_path_planning
import matplotrecorder


class RRT():
    u"""
    Class for RRT Planning
    """

    def __init__(self, start, goal, obstacleList, randArea,
                 goalSampleRate=10, maxIter=1000):
        u"""
        Setting Parameter

        start:Start Position [x,y]
        goal:Goal Position [x,y]
        obstacleList:obstacle Positions [[x,y,size],...]
        randArea:Ramdom Samping Area [min,max]

        """
        self.start = Node(start[0], start[1], start[2])
        self.end = Node(goal[0], goal[1], goal[2])
        self.minrand = randArea[0]
        self.maxrand = randArea[1]
        self.goalSampleRate = goalSampleRate
        self.maxIter = maxIter

    def Planning(self, animation=True):
        u"""
        Pathplanning

        animation: flag for animation on or off
        """

        self.nodeList = [self.start]
        for i in range(self.maxIter):
            rnd = self.get_random_point()
            nind = self.GetNearestListIndex(self.nodeList, rnd)

            newNode = self.steer(rnd, nind)

            if self.__CollisionCheck(newNode, obstacleList):
                self.nodeList.append(newNode)

            if animation:
                self.DrawGraph(rnd=rnd)

        # generate coruse
        lastIndex = self.get_best_last_index()
        #  print(lastIndex)
        path = self.gen_final_course(lastIndex)
        return path

    def choose_parent(self, newNode, nearinds):
        if len(nearinds) == 0:
            return newNode

        dlist = []
        for i in nearinds:
            dx = newNode.x - self.nodeList[i].x
            dy = newNode.y - self.nodeList[i].y
            d = math.sqrt(dx ** 2 + dy ** 2)
            theta = math.atan2(dy, dx)
            if self.check_collision_extend(self.nodeList[i], theta, d):
                dlist.append(self.nodeList[i].cost + d)
            else:
                dlist.append(float("inf"))

        mincost = min(dlist)
        minind = nearinds[dlist.index(mincost)]

        if mincost == float("inf"):
            print("mincost is inf")
            return newNode

        newNode.cost = mincost
        newNode.parent = minind

        return newNode

    def pi_2_pi(self, angle):
        while(angle >= math.pi):
            angle = angle - 2.0 * math.pi

        while(angle <= -math.pi):
            angle = angle + 2.0 * math.pi

        return angle

    def steer(self, rnd, nind):
        #  print(rnd)
        curvature = 1.0

        nearestNode = self.nodeList[nind]

        px, py, pyaw, mode, clen = dubins_path_planning.dubins_path_planning(
            nearestNode.x, nearestNode.y, nearestNode.yaw, rnd[0], rnd[1], rnd[2], curvature)

        newNode = copy.deepcopy(nearestNode)
        newNode.x = px[-1]
        newNode.y = py[-1]
        newNode.yaw = pyaw[-1]

        newNode.path_x = px
        newNode.path_y = py
        newNode.path_yaw = pyaw
        newNode.cost += clen
        newNode.parent = nind

        return newNode

    def get_random_point(self):

        if random.randint(0, 100) > self.goalSampleRate:
            rnd = [random.uniform(self.minrand, self.maxrand),
                   random.uniform(self.minrand, self.maxrand),
                   random.uniform(-math.pi, math.pi)
                   ]
        else:  # goal point sampling
            rnd = [self.end.x, self.end.y, self.end.yaw]

        return rnd

    def get_best_last_index(self):
        #  print("get_best_last_index")

        disglist = [self.calc_dist_to_goal(
            node.x, node.y) for node in self.nodeList]
        goalinds = [disglist.index(i) for i in disglist if i <= 0.1]
        #  print(goalinds)

        mincost = min([self.nodeList[i].cost for i in goalinds])
        for i in goalinds:
            if self.nodeList[i].cost == mincost:
                return i

        return None

    def gen_final_course(self, goalind):
        path = [[self.end.x, self.end.y]]
        while self.nodeList[goalind].parent is not None:
            node = self.nodeList[goalind]
            for (ix, iy) in zip(reversed(node.path_x), reversed(node.path_y)):
                path.append([ix, iy])
            #  path.append([node.x, node.y])
            goalind = node.parent
        path.append([self.start.x, self.start.y])
        return path

    def calc_dist_to_goal(self, x, y):
        return np.linalg.norm([x - self.end.x, y - self.end.y])

    def DrawGraph(self, rnd=None):
        u"""
        Draw Graph
        """
        import matplotlib.pyplot as plt
        plt.clf()
        if rnd is not None:
            plt.plot(rnd[0], rnd[1], "^k")
        for node in self.nodeList:
            if node.parent is not None:
                plt.plot(node.path_x, node.path_y, "-g")

        for (ox, oy, size) in obstacleList:
            plt.plot(ox, oy, "ok", ms=30 * size)

        dubins_path_planning.plot_arrow(
            self.start.x, self.start.y, self.start.yaw)
        dubins_path_planning.plot_arrow(
            self.end.x, self.end.y, self.end.yaw)

        plt.axis([-2, 15, -2, 15])
        plt.grid(True)
        plt.pause(0.01)
        matplotrecorder.save_frame()  # save each frame

    def GetNearestListIndex(self, nodeList, rnd):
        dlist = [(node.x - rnd[0]) ** 2 +
                 (node.y - rnd[1]) ** 2 +
                 (node.yaw - rnd[2] ** 2) for node in nodeList]
        minind = dlist.index(min(dlist))

        return minind

    def __CollisionCheck(self, node, obstacleList):

        for (ox, oy, size) in obstacleList:
            for (ix, iy) in zip(node.path_x, node.path_y):
                dx = ox - ix
                dy = oy - iy
                d = dx * dx + dy * dy
                if d <= size ** 2:
                    return False  # collision

        return True  # safe


class Node():
    u"""
    RRT Node
    """

    def __init__(self, x, y, yaw):
        self.x = x
        self.y = y
        self.yaw = yaw
        self.path_x = []
        self.path_y = []
        self.path_yaw = []
        self.cost = 0.0
        self.parent = None


if __name__ == '__main__':
    print("Start rrt start planning")
    import matplotlib.pyplot as plt
    # ====Search Path with RRT====
    obstacleList = [
        (5, 5, 1),
        (3, 6, 2),
        (3, 8, 2),
        (3, 10, 2),
        (7, 5, 2),
        (9, 5, 2)
    ]  # [x,y,size(radius)]

    # Set Initial parameters
    start = [0.0, 0.0, math.radians(0.0)]
    goal = [10.0, 10.0, math.radians(0.0)]

    rrt = RRT(start, goal, randArea=[-2.0, 15.0], obstacleList=obstacleList)
    path = rrt.Planning(animation=True)

    # Draw final path
    rrt.DrawGraph()
    plt.plot([x for (x, y) in path], [y for (x, y) in path], '-r')
    plt.grid(True)
    plt.pause(0.001)
    plt.show()

    matplotrecorder.save_movie("animation.gif", 0.1)