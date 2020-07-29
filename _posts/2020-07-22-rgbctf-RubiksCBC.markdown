---
layout: default
title:  "rgbctf2020 - RubiksCBC"
date:   2020-07-22 09:30:11 +0100
categories: rgbctf
---

## RubiksCBC

Description: 
>I implemented this really cool Rubiks CBC encryption algorithm and tested it on a document with my flag in it, but my dog ate my hard drive so I couldn't decrypt the file :(
>
>Luckily I backed up the encrypted file. Can you recover my data?

Category: *Cryptography*

First Blood: **1 hour, 36 minutes** after release  by team **aetjia**

To try out this challenge, download the file [here][rubik-dl]

### **The Problem**
We are given 2 files, a file of scrambled data and a README file.

>scramble("F", "OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR") 
> => "OOOOOOYYYYYRWWWOGGBBBYYRWWWOGGBBBYYRWWWOGGBBBGGGRRRRRR"
>
>==============================================================
>
>IV = "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuv"
>SCRAMBLE = D R2 F2 D B2 D2 R2 B2 D L2 D' R D B L2 B' L' R' B' F2 R2 D R2 B2 R2 D L2 D2 F2 R2 F' D' B2 D' B U B' L R' D'
>
>==============================================================

What can we gleam from this file:

- The example scramble and IV tells use that the cipher uses a block size of 54 bytes, one byte per tile on the rubiks cube.
- The algorithm must translate a flat block of data to a net of a cube in the following way:
{% highlight plaintext %}
OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR
{% endhighlight %}

{% highlight plaintext %}
        O O O
        O O O
        O O O

Y Y Y   W W W   G G G   B B B
Y Y Y   W W W   G G G   B B B
Y Y Y   W W W   G G G   B B B

        R R R
        R R R
        R R R
{% endhighlight %}
- That the encryption operation most likely is just a rubiks cube permutation of each block

### **Defining a Rubiks Cube in Python**
Keeping in mind we are in a CTF competition and solving the problem is time sensitive, lets build a quick and dirty rubiks class to represent movement of the cube.

First we need a way to translate a block into a rubiks cube net

{% highlight python %}
import numpy as np

class Cube(object): 

    dimensions = 3

    def __init__(self, block):
        assert len(block) == 54
        self.U = np.array([list(block[i:i+3]) for i in range(0,9,3)])
        self.L = np.array([list(block[i+9:i+12]) for i in range(0,33,12)]) 
        self.F = np.array([list(block[i+12:i+15]) for i in range(0,33,12)])
        self.R = np.array([list(block[i+15:i+18]) for i in range(0,33,12)]) 
        self.B = np.array([list(block[i+18:i+21]) for i in range(0,33,12)]) 
        self.D = np.array([list(block[i:i+3]) for i in range(45,54,3)]) 


    def flat_str(self):
        # Get the flat rubiks string in the same format as the input required to build the cube object
        out = "".join(self.U.flatten())
        out += "".join(np.array(list(zip(self.L,self.F,self.R,self.B))).flatten()) 
        out += "".join(self.D.flatten())
        return out


    def __str__(self):
        # Print the rubiks cube as a net
        indent = ' ' * self.dimensions + ' ' * (self.dimensions-1) + '\t'
        
        out = indent
        out += '\n{i}'.format(i=indent).join([' '.join([tile for tile in row]) for row in self.U]) + '\n\n'
        out += "\n".join(["\t".join([" ".join(r) for r in x]) for x in np.array(list(zip(self.L,self.F,self.R,self.B)))])
        out += "\n\n"
        out += indent
        out += '\n{i}'.format(i=indent).join([' '.join([tile for tile in row]) for row in self.D]) + '\n'
        return out


def main():
    c = Cube("OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR")
    print(c)
    print(c.flat_str())


if __name__=="__main__":
    main()
{% endhighlight %}

Lets test the above code

{% highlight shell %}
$ python3 cube.py 
     	O O O
     	O O O
     	O O O

Y Y Y	W W W	G G G	B B B
Y Y Y	W W W	G G G	B B B
Y Y Y	W W W	G G G	B B B

     	R R R
     	R R R
     	R R R

OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR
{% endhighlight %}

So we have a way to load a block into the cube net and out again.

The next step is to implement movement. The good news is that actually we can implement every possible move on a 3x3 rubiks cube with combinations of only 3 moves. We just need to be able to rotate a face, and to rotate the cube on 2 axes. More on this later. Add the below move functions to our class:

{% highlight python %}
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
{% endhighlight %}

For the `rot_x` and `rot_y` functions, we simply define rotating the entire cube on the X and Y axis. The numpy array has a convenient `rot90` function which handles rotating the tiles on a face, in `rot_F` we just need to worry about the tiles perpendicular to our rotated face tiles, you can see the code for this in the for loop in that function.

After some testing to confirm `rot_x`, `rot_y` and `rot_F` permute the cube how we expect, we can go about implementing the rest of the moves required for a barebones rubiks cube to work

{% highlight python %}
    # We define all other face rotations as combinations of x y and F

    def rot_B(self, prime=False):
        # B = 2y F 2y, B' = 2y F' 2y
        self.rot_y()
        self.rot_y()
        self.rot_F(prime)
        self.rot_y()
        self.rot_y()
    
    
    def rot_L(self, prime=False):
        # L = y' F y, L'= y' F' y
        self.rot_y(True)
        self.rot_F(prime)
        self.rot_y()
        

    def rot_R(self, prime=False):
        # R = y F y', R'= y F' y'
        self.rot_y()
        self.rot_F(prime)
        self.rot_y(True)
        
        
    def rot_U(self, prime=False):
        # U = x' F x, U' = x' F' x
        self.rot_x(True)
        self.rot_F(prime)
        self.rot_x()
        
        
    def rot_D(self, prime=False):
        # D = x F x', D' = x F' x'
        self.rot_x()
        self.rot_F(prime)
        self.rot_x(True)
{% endhighlight %}

If it isn't clear what is happening, it might become clear if you have a look at this [website](https://ruwix.com/the-rubiks-cube/notation/) or played around with one you have lying around. The point is, we can combine the moves `x`, `y` and `F` in such a way that we can define any other possible move on a rubiks cube. Take the `rot_U` function as an example:

`U` means "rotate the U face (upward face) 90 degrees clockwise" and `U'` means the same but counterclockwise. If we run the `x'` move first, however, the `U` face _becomes_ the `F` face, for which we have already defined rotation. From there it is as simple as running our `rot_F` function and returning the face to its `U` position by running `x`

After testing these to confirm they work we can move on to the final step: defining a way to apply an entire algorithm to the cube in one go.

{% highlight python %}
    def apply(self, move, prime=False):
        getattr(self, "rot_"+move[0])(prime)
    
    
    def scramble(self, scramble):
        # Takes a legal scramble, splits to moves and applies each.
        # if it contains a '2', do it twice
        for move in scramble.split(' '):
            m = move.replace("2", "")
            self.apply(m, "'" in move)
            if '2' in move:
                self.apply(m, "'" in move)
           
        
    def unscramble(self, scramble):
        # Takes a legal scramble, reverse it, splits to moves and applies the opposite of each.
        # if move contains a '2', do it twice
        for move in scramble.split(' ')[::-1]:
            m = move.replace("2", "")
            self.apply(m, not "'" in move) 
            if '2' in move:
                self.apply(m, not "'" in move)   
{% endhighlight %}

Lets test it:

{% highlight python %}
from cube import Cube 

cube = Cube("OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR")

alg = "F D' L D2 F' R U2 L2 B"

# Make the cube
print("fresh cube")
print(cube) 
print(cube.flat_str())

# Scramble
print("scrambling with", alg) 

cube.scramble(alg)

print(cube) 
print(cube.flat_str())

# Unscramble
print("unscrambling ", alg) 

cube.unscramble(alg) 

print(cube)
print(cube.flat_str())
{% endhighlight %}

Running the above script:

{% highlight plaintext %}
$ python3 test.py 

fresh cube
     	O O O
     	O O O
     	O O O

Y Y Y	W W W	G G G	B B B
Y Y Y	W W W	G G G	B B B
Y Y Y	W W W	G G G	B B B

     	R R R
     	R R R
     	R R R

OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRRR

scrambling with F D' L D2 F' R U2 L2 B
     	Y G G
     	R O B
     	R O R

O B B	G B G	W Y B	O O W
O Y W	G W W	R G R	G B W
Y R R	B O W	R G G	W W O

     	Y Y Y
     	Y R B
     	B Y O

YGGROBROROBBGBGWYBOOWOYWGWWRGRGBWYRRBOWRGGWWOYYYYRBBYO

unscrambling  F D' L D2 F' R U2 L2 B
     	O O O
     	O O O
     	O O O

Y Y Y	W W W	G G G	B B B
Y Y Y	W W W	G G G	B B B
Y Y Y	W W W	G G G	B B B

     	R R R
     	R R R
     	R R R

OOOOOOOOOYYYWWWGGGBBBYYYWWWGGGBBBYYYWWWGGGBBBRRRRRRRR
{% endhighlight %}

So as far as reasonable testing would demonstrate, this works. There is however one more small modification that needs to occur for our cube object to be used in the decryption algorithm we are about to implement: we need it to work with blocks of bytes not strings.

Specifically we want to construct a cube with 54 bytes of data, not 54 characters, and we want to be able to get the permutated bytes out again in the right format.

To do that we simply make sure our numpy arrays in the `__init__` function take bytes as a data type, and modify the `flat_str` function to get the bytes rather than a string.

{% highlight python %}
    def __init__(self, block):
        assert len(block) == 54
        self.U = np.array([list(block[i:i+3]) for i in range(0,9,3)], dtype=np.dtype('b'))
        self.L = np.array([list(block[i+9:i+12]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.F = np.array([list(block[i+12:i+15]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.R = np.array([list(block[i+15:i+18]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.B = np.array([list(block[i+18:i+21]) for i in range(0,33,12)], dtype=np.dtype('b'))
        self.D = np.array([list(block[i:i+3]) for i in range(45,54,3)], dtype=np.dtype('b'))


    def get_block_bytes(self):
        # Get the flat rubiks block in the same format as the input required to build the cube object
        out = b"".join(self.U.flatten())
        out += b"".join(np.array(list(zip(self.L,self.F,self.R,self.B))).flatten()) 
        out += b"".join(self.D.flatten())
        return out
{% endhighlight %}

Find the complete file [here][cube-py]

### **Implementing CBC Decryption**

Lets review CBC decryption to understand the algorithm we need to implement:

![cbc-dec-image]

So the process in steps is as follows:

1. Take the final cipher block and unscramble it
2. xor the unscrambled block with the previous cipher block
3. Save the plaintext
4. repeat with next cipher block

When we reach the first cipher block, xor with the IV

{% highlight python %}
from cube import Cube
import sys
from tqdm import tqdm   # fancy progress bar

BLOCK_SIZE=54
IV = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuv"
KEY = "D R2 F2 D B2 D2 R2 B2 D L2 D' R D B L2 B' L' R' B' F2 R2 D R2 B2 R2 D L2 D2 F2 R2 F' D' B2 D' B U B' L R' D'"


def byte_dec_block(block, key):
    c = Cube(block)
    c.unscramble(key)
    return c.get_block_bytes()


def xor(block, key):
    return bytes([b ^ k for b, k in zip(block, key)])


def byte_dec_file(file, iv, key):
    with open(file, "rb") as fp:
        data = fp.read()

    # Create a list of cipher blocks with the IV at the start
    cipher_blocks = [iv] + [data[i:i+BLOCK_SIZE] for i in range(0, len(data), BLOCK_SIZE)]

    # Create a list of empty lists to store the plaintext in
    plain_blocks = [[] for block in cipher_blocks[1:]]

    i = len(plain_blocks)

    for block in tqdm(cipher_blocks[1:][::-1]):                 # For each ciphertext block
        decrypt = byte_dec_block(block, key)                    # Decrypt (unscramble) with our key
        plain_blocks[i-1] = xor(decrypt, cipher_blocks[i-1])    # xor the decrypted block with the previous cipher block
        i -= 1

    with open("dec_" + file.split('.')[0], "wb") as fp:
        fp.write(b"".join(plain_blocks))


def main():
    byte_dec_file(sys.argv[-1], IV, KEY)


if __name__=="__main__":
	main()
{% endhighlight %}

Running the above code against the encrypted data successfully decrypts a valid PDF, see the test below:

{% highlight shell %}
$ python3 dec.py encrypted_pdf 
100%|██████████████████████████████████████████████████| 517/517 [00:03<00:00, 168.36it/s]
$ file dec_encrypted_pdf 
dec_encrypted_pdf: PDF document, version 1.5
{% endhighlight %}

The [decrypted document][dec-document] is RFC 2549, IP Over Avian Carriers with QoS. On page 4 there is a QR code containing the flag.


![flag_qr]

Flag: `rgbCTF{!IP_over_Avian_Carriers_with_QoS!}`

### **Afterword**

If you want to play around with this toy cipher, you can access the code used for encryption and decryption in [this repository][rubikciphergit] . Otherwise if its the simple rubiks cube implementation you are looking for, you can access it from the link in this post or from [this repository][simplerubikgit]

[cbc-dec-image]: /assets/images/rgbctf/rubiks/cbc-dec-image.png
[flag_qr]: /assets/images/rgbctf/rubiks/flag_qr.png

[cube-py]: /assets/files/rgbctf/rubikscbc/cube.py
[dec-document]: /assets/files/rgbctf/rubikscbc/decrypted.pdf

[rubikciphergit]: https://github.com/klanec/RubiksCipher
[simplerubikgit]: https://github.com/klanec/SimpleRubik

[rubik-dl]: https://drive.google.com/uc?export=download&id=1t_o2MVO0x-WtJRguCEYbHgmCoWFf3KDn