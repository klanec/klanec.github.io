import numpy as np


class Cube(object): 
    dimensions = 3
    

    def __init__(self, block):
        assert len(block) == 54
        self.U = np.array([list(block[i:i+3]) for i in range(0,9,3)], dtype=np.dtype('b'))
        self.L = np.array([list(block[i+9:i+12]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.F = np.array([list(block[i+12:i+15]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.R = np.array([list(block[i+15:i+18]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.B = np.array([list(block[i+18:i+21]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.D = np.array([list(block[i:i+3]) for i in range(45,54,3)], dtype=np.dtype('b'))


    def rot_x(self, prime=False):
        '''Rotates the entire cube on R face.
        Anticlockwise rotation is simply clockwise rotation * 3
        '''
        for i in range(3 if prime else 1):
            bufU = self.U
            self.U = self.F
            self.F = self.D
            self.D = self.B[::-1,::-1]
            self.B = bufU[::-1,::-1]
            self.R = np.rot90(self.R, k=-1)
            self.L = np.rot90(self.L, k=1)
    

    def rot_y(self, prime=False): 
        '''Rotates the entire cube on U face.
        Anticlockwise rotation is simply clockwise rotation * 3
        '''
        for i in range(3 if prime else 1):
            bufF = self.F
            self.F = self.R
            self.R = self.B
            self.B = self.L
            self.L = bufF
            self.U = np.rot90(self.U, k=-1)
            self.D = np.rot90(self.D, k=1)
     

    def rot_F(self, prime=False):    
        '''Rotates face F
        Anticlockwise rotation is simply clockwise rotation * 3
        '''
        self.F = np.rot90(self.F, k=1 if prime else -1)

        for i in range(3 if prime else 1):
            buf = self.L[:, -1].copy()
            self.L[:, -1] = self.D[0]
            self.D[0] = self.R[:, 0][::-1]
            self.R[:, 0] = self.U[-1]
            self.U[-1] = buf[::-1]
            

    # We define all other face rotations as combinations of x y and F

    def rot_B(self, prime=False):
        # B = 2y F 2y
        # B' = 2y F' 2y
        self.rot_y()
        self.rot_y()
        self.rot_F(prime)
        self.rot_y()
        self.rot_y()
    
    
    def rot_L(self, prime=False):
        # L = y' F y
        # L'= y' F' y
        self.rot_y(True)
        self.rot_F(prime)
        self.rot_y()
        

    def rot_R(self, prime=False):
        # R = y F y'
        # R'= y F' y'
        self.rot_y()
        self.rot_F(prime)
        self.rot_y(True)
        
        
    def rot_U(self, prime=False):
        # U = x' F x
        # U' = x' F' x
        self.rot_x(True)
        self.rot_F(prime)
        self.rot_x()
        
        
    def rot_D(self, prime=False):
        # D = x F x'
        # D' = x F' x'
        self.rot_x()
        self.rot_F(prime)
        self.rot_x(True)
        

    def apply(self, move, prime=False):
        getattr(self, "rot_"+move[0])(prime)
    
    
    def scramble(self, scramble):
        # Take each move and apply it, if it contains a'2', do it again
        for move in scramble.split(' '):
            m = move.replace("2", "")
            self.apply(m, "'" in move)
            if '2' in move:
                self.apply(m, "'" in move)
           
        
    def unscramble(self, scramble):
        # Take the reversed move list, if no '2' in move, do the reverse, other
        for move in scramble.split(' ')[::-1]:
            m = move.replace("2", "")
            self.apply(m, not "'" in move) 
            if '2' in move:
                self.apply(m, not "'" in move)                           
    
    
    def get_block_bytes(self):
        out = b"".join(self.U.flatten())
        out +=b"".join(np.array(list(zip(self.L,self.F,self.R,self.B))).flatten()) 
        out += b"".join(self.D.flatten())
        return out

    def __str__(self):
        indent = ' ' * self.dimensions + ' ' * (self.dimensions-1) + '\t'
        
        out = indent
        out += '\n{i}'.format(i=indent).join([' '.join([tile for tile in row]) for row in self.U]) + '\n\n'
        out += "\n".join(["\t".join([" ".join(r) for r in x]) for x in np.array(list(zip(self.L,self.F,self.R,self.B)))])
        out += "\n\n"
        out += indent
        out += '\n{i}'.format(i=indent).join([' '.join([tile for tile in row]) for row in self.D]) + '\n'
        return out