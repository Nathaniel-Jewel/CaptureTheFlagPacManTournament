from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util
from game import Directions, Actions
import game
import capture
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'Defense', second = 'Offense'):
  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

class functions(CaptureAgent):

    def registerInitialState(self, state):

        CaptureAgent.registerInitialState(self, state)
        self.walls = state.getWalls().data
        self.height = state.getWalls().height
        self.width = state.getWalls().width
        self.bases = self.getMid()
        self.fleeing = False
        self.eating = True
        self.moving = False
        self.goto_base = (0, 0)
        self.startPos = state.getAgentState(self.index).getPosition()
        self.enemyStartPos = [state.getAgentState(i).getPosition() for i in self.getOpponents(state)][0]
        self.sequence = []
        self.knownFoods = self.getFoodYouAreDefending(state)
        self.lastInvader = []
        self.find_dead_ends()

    def choose(self, state, list):
        if len(list) is 0:
            return 0

        closest = float('Inf')
        best = None
        myPos = state.getAgentState(self.index).getPosition()
        for base in list:
            temp = self.getMazeDistance(base, myPos)
            if temp < closest:
                closest = temp
                best = base
        return best

    def goto(self, state, target):
        return int(state.getAgentState(self.index).getPosition()[0]) is target[0] \
                and (int(state.getAgentState(self.index).getPosition()[1]) is target[1])

    def pickBase(self, myPos):
        base2 = None
        farthest = -float('Inf')
        for base in self.bases:
            if self.getMazeDistance(myPos, base) > farthest:
                base2 = base
        self.goto_base = base2

    def find_dead_ends(self):
        self.deadEnds = {}
        corners = []

        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                pos = (x, y)
                if len(self.getNeighbors(pos)) == 1:
                    corners.append(pos)

        for corner in corners:
            neighbors = self.getNeighbors(corner)
            positions = []

            while len(neighbors) > 0 and len(neighbors) <= 2 and corner not in positions:
                positions.append(corner)
                for neighbor in neighbors:
                    if neighbor not in positions:
                        corner = neighbor
                neighbors = self.getNeighbors(corner)

            if len(neighbors) >= 3:
                for position in positions:
                    self.deadEnds[position] = corner

    def getNeighbors(self, pos):

        neighborList = []
        x = int(pos[0])
        y = int(pos[1])
        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        if self.walls[x][y]:
            return []

        for move in moves:
            nextX = x + move[0]
            nextY = y + move[1]
            if nextX > 0 and nextX < self.width and nextY > 0 and nextY < self.height:
                if not self.walls[nextX][nextY]:
                    neighborList.append((nextX, nextY))

        return neighborList

    def getMid(self):
        bases = []
        middle = self.width / 2

        if self.red:
            middle -= 1

        for y in range(1, self.height - 1):
            if not self.walls[middle][y]:
                bases.append((middle, y))
        return bases

    def compareFoods(self, old, new):

        foods = []
        for x in range(old.width):
            for y in range(old.height):
                if old[x][y] and not new[x][y]:
                    foods.append((x, y))

        return foods

    def getUnscaredEnemy(self, state):

        enemyPositions = []

        for index in self.getOpponents(state):
            enemyState = state.getAgentState(index)
            pos = enemyState.getPosition()
            if not enemyState.isPacman and pos is not None and enemyState.scaredTimer <= 1:
                enemyPositions.append(pos)

        return enemyPositions

    def getInvaders(self, state):

        enemyPos = self.compareFoods(self.knownFoods, self.getFoodYouAreDefending(state))

        for index in self.getOpponents(state):
            enemyState = state.getAgentState(index)
            pos = enemyState.getPosition()
            if enemyState.isPacman and pos is not None and pos not in enemyPos:
                enemyPos.append(pos)

        return enemyPos


    def find_closest(self, source, targets):

        distance = float('Inf')
        closest = None

        for target in targets:
            if self.getMazeDistance(source, target) < distance:
                closest = target
                distance = self.getMazeDistance(source, target)

        return closest

    def isPacman(self, pos):
        if self.red:
            return pos[0] > self.bases[0][0]
        else:
            return pos[0] < self.bases[0][0]



    #####################################################################

    # DEFENSE START

    #####################################################################
    def defensiveMove(self, state, target):

        actions = state.getLegalActions(self.index)
        if len(actions) == 0:
            return 0
        best = [None]
        distance = float('Inf')

        for action in actions:
            nextPos = Actions.getSuccessor(state.getAgentState(self.index).getPosition(), action)
            if not self.isPacman(nextPos):
                if self.getMazeDistance(target, nextPos) <  distance:
                    distance = self.getMazeDistance(target, nextPos)
                    best = [action]
                if self.getMazeDistance(target, nextPos) == distance:
                    best.append(action)

        return random.choice(best)

    def defend(self, state):

        myPos = state.getAgentState(self.index).getPosition()
        enemies = self.getInvaders(state)
        closestEnemy = self.find_closest(myPos, enemies)


        if closestEnemy is not None:
            self.lastInvader = []
            self.lastInvader.append(closestEnemy)
            return self.defensiveMove(state, closestEnemy)
        else:
            closestEnemy = self.find_closest(myPos, self.lastInvader)
            if closestEnemy is not None:
                return self.defensiveMove(state, closestEnemy)
            else:
                '''
                #some code that gives me good information, but i dont know how to use
                if self.red:
                    index = state.getRedTeamIndices()

                else:
                    index = state.getBlueTeamIndices()
                index.remove(self.index)

                one = util.manhattanDistance(state.getAgentState(self.index).getPosition(),
                                             state.getAgentState(index[0]).getPosition())
                lists = state.getAgentDistances()

                for list in lists:
                    if ((list - one)<= 6) and ((list - one) >= -6):
                        lists.remove(list)
                    elif (list <= 6) and (list >= -6):
                        lists.remove(list)

                print lists
                '''
                #print "no idea were is enemy"
                mostPossibleFood = self.find_closest(self.enemyStartPos, self.getFoodYouAreDefending(state).asList())
                return self.defensiveMove(state, mostPossibleFood)
    #####################################################################

    # DEFENSE END

    #####################################################################

    #####################################################################

    # OFFENSE START

    #####################################################################
    def aStar(self, start, target, safe):

        visited = []
        queue = util.PriorityQueue()
        queue.push((start, []), 0)

        while not queue.isEmpty():
            pos, path = queue.pop()

            if pos == target:
                return path

            if not pos in visited:
                neighbors = self.getNeighbors(pos)
                for neighbor in neighbors:
                    if not neighbor in visited:
                        if not safe or not self.isPacman(neighbor):
                            newPath = path + [neighbor]
                            queue.push((neighbor, newPath), util.manhattanDistance(neighbor, target))

            visited.append(pos)

        return []

    def sequenceActions(self, state):
        if len(self.sequence) is 0:
            basearray = []
            for base in self.bases:
                if self.getMazeDistance(state.getAgentState(self.index).getPosition(), base) > 6:
                    basearray.append(base)
            self.goto_base = random.choice(basearray)
            self.sequence = self.aStar(state.getAgentState(self.index).getPosition(), self.goto_base, True)
            return self.sequenceActions(state)

        actions = state.getLegalActions(self.index)
        for action in actions:
            next = Actions.getSuccessor(state.getAgentState(self.index).getPosition(), action)
            if int(next[0]) is self.sequence[0][0] and int(next[1]) is self.sequence[0][1]:
                del self.sequence[0]
                if len(self.sequence) is 0:
                    self.eating = True
                    self.moving = False
                    self.fleeing = False
                return action

    def offensiveMove(self, state, target, string):
        if string is "eat":
            self.eating = True
            self.moving = False
            self.fleeing = False
        if string is "move":
            self.eating = False
            self.moving = True
            self.fleeing = False
            if len(self.sequence) is 0:
                self.sequence = self.aStar(state.getAgentState(self.index).getPosition(), target, True)
                return self.sequenceActions(state)

        if string is "flee":
            self.eating = False
            self.moving = False
            self.fleeing = True

        actions = state.getLegalActions(self.index)
        if len(actions) == 0:
            return 0

        best = []
        enemies = self.getUnscaredEnemy(state)

        minDistance = float('Inf')
        minEnemyDis = float('Inf')

        if self.moving:
            return 0

        for action in actions:
            nextPos = Actions.getSuccessor(state.getAgentState(self.index).getPosition(), action)
            closetEnemy = self.find_closest(nextPos, enemies)
            distance = self.getMazeDistance(target, nextPos)

            if distance < minDistance:
                best = [action]
                minDistance = distance

                if closetEnemy is None:
                    minEnemyDis = float('Inf')
                else:
                    minEnemyDis = self.getMazeDistance(nextPos, closetEnemy)

            elif distance == minDistance:
                if closetEnemy is None:
                    best.append(action)
                elif self.getMazeDistance(nextPos, closetEnemy) > minEnemyDis:
                    best = [action]
                    minDistance= distance
                    minEnemyDis = self.getMazeDistance(nextPos, closetEnemy)


        return random.choice(best)


    def offend(self, state):
        foods = []
        myPos = state.getAgentState(self.index).getPosition()
        closetEnemy = self.find_closest(myPos, self.getUnscaredEnemy(state))
        capsules = self.getCapsules(state)

        if closetEnemy is None:
            foods = self.getFood(state).asList()
            if len(capsules) > 0:
                for cap in capsules:
                    foods.append(cap)
        else:
            temp = self.getFood(state).asList()
            if len(temp) is 3:
                for food in temp:
                    if self.getMazeDistance(myPos, food) < self.getMazeDistance(closetEnemy, food):
                        foods.append(food)
            else:
                if len(capsules) > 0:
                    for cap in capsules:
                        temp.append(cap)
                for food in temp:
                    if self.getMazeDistance(myPos, food) < self.getMazeDistance(closetEnemy, food):
                        if self.getMazeDistance(myPos, closetEnemy) > 4:
                            foods.append(food)
                        else:
                            if len(capsules) > 0:
                                for cap in capsules:
                                    foods.append(cap)
                            if food not in self.deadEnds:
                                foods.append(food)

        food_target = self.choose(state, foods)
        base_target = self.choose(state, self.bases)

        if self.fleeing:
            if closetEnemy is None:
                return self.offensiveMove(state, food_target, "eat")
            there = self.goto(state, base_target)
            if there or not self.isPacman:
                self.pickBase(myPos)
                return self.offensiveMove(state, self.goto_base, "move")
            else:
                return self.offensiveMove(state, base_target, "flee")

        if self.eating:
            closetEnemy = self.find_closest(myPos, self.getUnscaredEnemy(state))

            if food_target is 0 and closetEnemy is not None:
                if self.isPacman:
                    return self.offensiveMove(state, base_target, "flee")
                else:
                    self.pickBase(myPos)
                    return self.offensiveMove(state, self.goto_base, "move")

            if closetEnemy is not None and self.isPacman:
                if self.getMazeDistance(myPos, base_target) < 5:
                    if self.getMazeDistance(myPos, closetEnemy) < 2 and \
                        self.getMazeDistance(closetEnemy, base_target) > self.getMazeDistance(myPos, base_target):
                        return self.offensiveMove(state, base_target, "flee")
            return self.offensiveMove(state, food_target, "eat")
        return self.offensiveMove(state, food_target, "eat")


    #####################################################################

    # OFFENSE END

    #####################################################################

    #####################################################################

    # AVOID START

    #####################################################################

    def avoidMove(self, state, target):
        if target is None:
            return None

        actions = state.getLegalActions(self.index)
        if len(actions) == 0:
            return 0
        best = [None]

        if self.getMazeDistance(target, state.getAgentState(self.index).getPosition()) > 3:
            distance = float('Inf')
        else:
            distance = -float('Inf')
        for action in actions:
            nextPos = Actions.getSuccessor(state.getAgentState(self.index).getPosition(), action)
            # should not move to enemy's side
            if not self.isPacman(nextPos):
                if self.getMazeDistance(target, nextPos) > 3:
                    if self.getMazeDistance(target, nextPos) < distance:
                        distance = self.getMazeDistance(target, nextPos)
                        best = [action]
                    if self.getMazeDistance(target, nextPos) == distance:
                        best.append(action)
                else:
                    if self.getMazeDistance(target, nextPos) > distance:
                        distance = self.getMazeDistance(target, nextPos)
                        best = [action]
                    if self.getMazeDistance(target, nextPos) == distance:
                        best.append(action)

        return random.choice(best)

    def avoid(self, state):
        myPos = state.getAgentState(self.index).getPosition()
        enemies = self.getInvaders(state)
        closetEmemy = self.find_closest(myPos, enemies)

        if closetEmemy is not None:
            self.lastInvader = []
            self.lastInvader.append(closetEmemy)
            return self.avoidMove(state, closetEmemy)
        else:
            closetEmemy = self.find_closest(myPos, self.lastInvader)
            if closetEmemy is not None:

                return self.avoidMove(state, closetEmemy)
            else:
                mostPossibleFood = self.find_closest(self.enemyStartPos,
                                                     self.getFoodYouAreDefending(state).asList())
                return self.avoidMove(state, mostPossibleFood)

    #####################################################################

    # AVOID END

    #####################################################################

class Defense(functions):
    def chooseAction(self, state):
        ownState = state.getAgentState(self.index)
        scaredTimer = ownState.scaredTimer

        if scaredTimer > 0:
            action = self.avoid(state)

        else:
            action = self.defend(state)

        self.knownFoods = self.getFoodYouAreDefending(state)
        if len(self.getInvaders(state)) > 0:
            self.lastInvader = self.getInvaders(state)
        if len(self.lastInvader) is 1:
            if self.getMazeDistance(state.getAgentState(self.index).getPosition(), self.lastInvader[0]) is 0:
                self.lastInvader = []

        return action

class Offense(functions):

    def chooseAction(self, state):
        if len(self.sequence) > 0:
            action = self.sequenceActions(state)
        else:
            action = self.offend(state)

        self.knownFoods = self.getFoodYouAreDefending(state)
        if len(self.getInvaders(state)) > 0:
            self.lastInvader = self.getInvaders(state)
        if len(self.lastInvader) is 1:
            if self.getMazeDistance(state.getAgentState(self.index).getPosition(), self.lastInvader[0]) is 0:
                self.lastInvader = []
        if action is None or action is 0:
            action = random.choice(state.getLegalActions(self.index))
        return action