import asyncio
import getpass
import json
from logging import currentframe
import os
from tree_search import *
from game import *
from shape import SHAPES
import traceback
import cProfile

import websockets

previousGrid, globalGoal, globalPath, globalScore, prev, globalStart, cnt, turns, game, piece, rotation, allPieces, gridWithPiece,firstcnt,fail = [0], [] , [] , 0, [], False, 0 , [0,0], 0, 0, False, [], [], 0,0

async def agent_loop(server_address="localhost:8000", agent_name="student"):

    
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game update, this must be called timely or your game will get out of sync with the server
                key = ""
                global previousGrid, globalGoal, globalScore, globalPath, prev, game, cnt, turns, globalStart, piece, rotation, gridWithPiece, firstcnt,fail
                #Ignora a primeira mensagem
                try: 
                    #verifica se houve uma atualização na grid do jogo, ou seja, se a peça já caiu 
                    if( previousGrid != state["game"]):  
                        previousGrid, cnt, globalScore, turns, globalStart, allPieces, rotation = state["game"].copy(), 0, 0, [0,0], False, [], True
                    elif(state["piece"] != None and rotation):
                        provPiece =[ [state["piece"][0][0]-2, state["piece"][0][1]-1], \
                                     [state["piece"][1][0]-2, state["piece"][1][1]-1], \
                                     [state["piece"][2][0]-2, state["piece"][2][1]-1], \
                                     [state["piece"][3][0]-2, state["piece"][3][1]-1] ]

                        prov = { tuple(a) for a in provPiece}
                        provPiece = prov
                        for s in SHAPES :
                            tmp = set()
                            for a in s.positions:
                                tmp.add(tuple(a))
                            tmp = { tuple(a) for a in s.positions}
                            if provPiece == tmp:
                                allPieces.append(s)
                                break      
                        """for b in state["next_pieces"]:
                            b =[ (b[0][0], b[0][1]), \
                                     (b[1][0], b[1][1]), \
                                     (b[2][0], b[2][1]), \
                                     (b[3][0], b[3][1]) ]
                            prov = set()
                            for a in b:
                                prov.add(tuple(a))  
                            b = prov
                            for s in SHAPES :
                                tmp = { tuple(a) for a in s.positions}
                                if b == tmp:
                                    allPieces.append(s)
                                    break       
                                n=0   
                                while(n < 4 ):
                                    n+=1
                                    s.rotate()
                                    tmp = { tuple(a) for a in s.positions}
                                    if b == list(tmp):
                                        allPieces.append(s)
                                        break   """
                        rotation = False

                    #faz faz todas as rotação até voltar à inicial
                    elif cnt < 1:
                        if firstcnt < 4: 
                            bestgame = Tetris(state["game"],state["piece"])
                            globalGoal = bestgame.best().copy()
                            if(globalScore==0): 
                                globalScore=-10000000
                            if( bestgame.score > globalScore):
                                    game = bestgame
                                    turns[0]=firstcnt
                                    globalScore = game.score
                            if(firstcnt == 3) : 
                                cnt=2
                                globalStart=True
                            firstcnt+=1
                            await websocket.send(
                                    json.dumps({"cmd": "key", "key": "w"})
                                    )  # send key command to server - you must implement this send in the AI agent
                        else: 
                            while cnt < 4 : 
                                cnt1=0
                                provPiece = allPieces[0].positions
                                provPiece =[[provPiece[0][0]+2, provPiece[0][1]+2],\
                                            [provPiece[1][0]+2, provPiece[1][1]+2],\
                                            [provPiece[2][0]+2, provPiece[2][1]+2],\
                                            [provPiece[3][0]+2, provPiece[3][1]+2] ]
                                bestgame = Tetris(state["game"],provPiece)
                                globalGoal = bestgame.best().copy()
                                if(globalScore==0): 
                                    globalScore=-10000000
                                if( bestgame.score > globalScore):
                                        game = bestgame
                                        turns[0]=cnt
                                        gridWithPiece = game.test
                                        globalScore = game.score
                                """while cnt1 < len(allPieces[1].plan):
                                    provPiece = allPieces[1].positions
                                    provPiece =[[provPiece[0][0]+2, provPiece[0][1]+2],\
                                                [provPiece[1][0]+2, provPiece[1][1]+2],\
                                                [provPiece[2][0]+2, provPiece[2][1]+2],\
                                                [provPiece[3][0]+2, provPiece[3][1]+2] ]
                                    game1 = Tetris(gridWithPiece,provPiece)
                                    goal = game1.best().copy()
                                    if( bestgame.score+game1.score > globalScore):
                                        game = bestgame
                                        turns[0]=cnt
                                        turns[1]=cnt1
                                        globalScore = game.score+game1.score
                                    cnt1+=1
                                    allPieces[1].rotate()"""
                                #atualiza o bestScore, caso seja maior, e o numero de rotação necessarias para essa posição desse mesmo bestscore
                                if(cnt ==  3 ) : 
                                    globalStart=True
                                cnt+=1
                                allPieces[0].rotate()
                    #vai buscar o path para a melhor posição da melhor rotação
                    elif turns[0] > 0:
                        await websocket.send(
                            json.dumps({"cmd": "key", "key": "w"})
                            )  # send key command to server - you must implement this send in the AI agent
                        turns[0]-=1
                    elif  globalStart and globalGoal != None and globalGoal != []:
                        globalGoal=game.best().copy()
                        """print(tuple(globalGoal))
                        print(globalGoal)"""
                        p = SearchProblem(game,game.piece,globalGoal)      
                        t = SearchTree(p,'a*')
                        prev=game.piece
                        globalPath=t.search() 
                        if(globalPath != None) : globalPath.pop(0) 
                        globalStart=False
                    elif globalPath != None and globalPath != []:   
                        #percorre o path com os movimentos necessarios
                        nex = globalPath.pop(0)
                        key=game.cost(state["piece"],(prev,nex))
                        prev = nex
                        globalScore=0
                        await websocket.send(
                            json.dumps({"cmd": "key", "key": key})
                        )  # send key command to server - you must implement this send in the AI agent
                    elif  globalPath == []:
                        await websocket.send(
                            json.dumps({"cmd": "key", "key": "s"})
                        )  # send key command to server - you must implement this send in the AI agent
                except Exception:
                    traceback.print_exc()
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

                
class Tetris(SearchDomain):
    def __init__(self, grid, piece):
        def moves(piece,cost,left,right):
            if piece == None:
                return None
            elif left:
                #verifica se a peça, antes do movimento, bate na parede ou no final da grelha
                if 9 > piece[0][0]-1 != 0 and 9 > piece[1][0]-1 != 0 and 9 > piece[2][0]-1 != 0 and 9 > piece[3][0]-1 != 0:
                    if piece[0][1]+1 < 30 and piece[1][1]+1 < 30 and piece[2][1]+1 < 30 and piece[3][1]+1 < 30:
                        tmp = [ a.copy() for a in piece]            
                        #move a peça para a esquerda         
                        tmp [0][0] = tmp[0][0]-1
                        tmp [1][0] = tmp[1][0]-1
                        tmp [2][0] = tmp[2][0]-1
                        tmp [3][0] = tmp[3][0]-1
                        tmp [0][1] = tmp[0][1]+1
                        tmp [1][1] = tmp[1][1]+1
                        tmp [2][1] = tmp[2][1]+1
                        tmp [3][1] = tmp[3][1]+1  
                        for a in tuple(self.grid):
                            for b in tmp:
                                if a == b:
                                    return None
                        n = []
                        for a in tmp:
                            n.append(a[0])
                        #verifica se a peça está no occupied
                        if n not in self.occupied:
                            self.occupied.append(n)
                            self.futurePos.append(tmp)
                        currentCost=cost + "a"
                        self.moves.append((piece, tmp, "a"))
                        #volta a mover a peça para a esqueda
                        moves(tmp,currentCost,True,False)
            #verifica se a peça, antes do movimento, bate na parede ou no final da grelha
            elif right:
                if 9 > piece[0][0]+1 > 0 and 9 > piece[1][0]+1 > 0 and 9 > piece[2][0]+1 > 0 and 9 > piece[3][0]+1 > 0: 
                    if piece[0][1]+1 < 30 and piece[1][1]+1 < 30 and piece[2][1]+1 < 30 and piece[3][1]+1 < 30:
                        tmp = [ a.copy() for a in piece]                      
                        tmp [0][0] = tmp[0][0]+1
                        tmp [1][0] = tmp[1][0]+1
                        tmp [2][0] = tmp[2][0]+1
                        tmp [3][0] = tmp[3][0]+1
                        tmp [0][1] = tmp[0][1]+1
                        tmp [1][1] = tmp[1][1]+1
                        tmp [2][1] = tmp[2][1]+1
                        tmp [3][1] = tmp[3][1]+1  
                        for a in tuple(self.grid):
                            for b in tmp:
                                if a == b:
                                    return None
                        n = []
                        for a in tmp:
                            n.append(a[0])
                        if n not in self.occupied:
                            self.occupied.append(n)
                            self.futurePos.append(tmp)
                        currentCost=cost + "d"
                        self.moves.append((piece, tmp, "d"))
                        moves(tmp,currentCost,False,True)

        self.piece=piece    #peça
        self.grid = grid    #grelha de jogo
        self.futurePos=[]   #futuras posições possiveis
        self.occupied=[]    #colunas que já tenham uma posição no futurePos
        self.moves=[]       #moviemntos onde (c1, c2, d) --> c1-posição antes do movimento  // c2-posição depois do movimento // d-movimento(a-esquerda, d-direita)
        self.bestPos=[]     #melhor posição, ou seja, com melhor score
        self.test=[]
        #adiciona a primeira posição ao futurePos se não estiver nas posições ocupadas
        if piece != None :
            n = [ a[0] for a in piece]
        if n not in self.occupied:
            self.occupied.append(n)
        self.futurePos.append(piece)
        moves(piece,"",False,True)      #testa todas as posições com movimento para a direita
        moves(piece,"",True,False)      #testa todas as posições com movimento para a esquerda

    def best(self):
        def scoreVals(futGrid):
            res=[0,0,0,0]
            arrPos=[0]*30
            biggest = [30] *10
            numPieces = [0] *10
            futGridSet = list(set(map(tuple, futGrid)))
            for a in futGridSet:
                arrPos[a[1]] += 1
                if biggest[a[0]] > a[1] : biggest[a[0]]=a[1]
                if arrPos[a[1]] == 8: res[1]+=1  #completed lines
                numPieces[a[0]] += 1

            cnt =0
            for a in biggest:
                biggest[cnt]=30-a
                res[0] += biggest[cnt]   #aggHeight
                if( 9 > cnt > 0 ): res[2] += (biggest[cnt] - numPieces[cnt])  #holes
                if( 9 > cnt > 1 ): res[3] += abs( biggest[cnt-1] - biggest[cnt])  #bumpiness
                cnt+=1
            return res
        # puxa todas as posiç~~oes futuras para baixo, ou seja, onde estas vão ficar na grelha
        pullDown = []
        biggest = [30] *10
        for a in self.grid:
            if biggest[a[0]] > a[1]: biggest[a[0]]=a[1]
        x = 0
        for a in self.futurePos:
            tmp = [ b.copy() for b in a ]
            pullDown.append(tmp)
            tmp=pullDown[x]
            while tmp[0][1]+1 < biggest[tmp[0][0]] and tmp[1][1]+1 < biggest[tmp[1][0]] and tmp[2][1]+1 < biggest[tmp[2][0]] and tmp[3][1]+1 < biggest[tmp[3][0]]:
                tmp [0][1] = tmp[0][1]+1
                tmp [1][1] = tmp[1][1]+1
                tmp [2][1] = tmp[2][1]+1
                tmp [3][1] = tmp[3][1]+1
            x+=1
        
        #vai veriificar qual das posições do futurePos vai ter o melhor score
        bestScore = float("-inf")
        for a in pullDown:
            futGrid= self.grid.copy()
            nearWall=0
            for b in a:
                futGrid.append(b)
                if b[0] == 1 or b[0] == 8: nearWall+=1
            heu = scoreVals(futGrid)
            score =  -0.510066*(heu[0]-heu[1]*8) + 0.760666*heu[1] - 0.45*heu[2] - 0.184483*heu[3] + 0.14*nearWall
            #print(heu)
            if(score > bestScore):
                bestScore = score
                self.test = futGrid
                self.bestPos = a
        self.score=bestScore
        if self.bestPos == []: return []
        self.bestPos=self.futurePos[pullDown.index(self.bestPos)]
        return self.bestPos

    def actions(self,piece):
        actlist = []
        for (C1,C2,D) in self.moves:
            if (C1==piece):
                actlist += [(C1,C2)]
        return actlist 
    def result(self,piece,action):
        (C1,C2) = action
        if C1==piece:
            return C2
    def cost(self, piece, action):
        (C3,C4) = action
        for (C1,C2,D) in self.moves:
            if C1 == C3 and C2 == C4:
                return D
        return ""
    def heuristic(self, goal):
        for (C1,C2,D) in self.moves:
            if C2 == goal:
                return self.score
        return 0
    def satisfies(self, piece, goal):
        return goal==piece
                    

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
#cProfile.run('loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))')